import re
from typing import Optional
from enum import Enum
from pydantic import BaseModel


class SafetyAction(str, Enum):
    PASS = "pass"
    BLOCK = "block"
    MASK = "mask"
    WARN = "warn"


class SafetyPolicy(BaseModel):
    check_injection: bool = True
    check_pii: bool = True
    check_sensitive: bool = True
    check_compliance: bool = False
    pii_mask_strategy: str = "partial"  # partial, full, hash
    sensitivity_level: str = "medium"  # low, medium, high


class SafetyIssue(BaseModel):
    type: str
    detail: str
    severity: str = "medium"
    action: SafetyAction = SafetyAction.WARN


class SafetyResult(BaseModel):
    safe: bool
    issues: list[SafetyIssue] = []
    filtered_content: Optional[str] = None
    action: SafetyAction = SafetyAction.PASS
    reason: Optional[str] = None


class PIIEntity(BaseModel):
    """检测到的 PII 实体，包含位置信息用于脱敏"""
    pii_type: str
    value: str
    start: int
    end: int
    masked: str


class SafetyEngine:
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r'(?i)ignore\s+(all\s+)?previous\s+instructions',
        r'(?i)ignore\s+(all\s+)?above\s+instructions',
        r'(?i)disregard\s+(all\s+)?prior\s+(instructions|context)',
        r'(?i)you\s+are\s+now\s+(a|an)\s+',
        r'(?i)new\s+instructions?\s*:',
        r'(?i)system\s*:\s*you\s+are',
        r'(?i)override\s+(system|safety)\s+(prompt|instructions)',
        r'(?i)\[system\]\s*you\s+are',
        r'(?i)act\s+as\s+if\s+you\s+(have|are)\s+no\s+(restrictions|limitations)',
        # Broader multi-word injection patterns
        r"(?i)(ignore|forget|disregard|override|bypass)\s+(all\s+)?(previous|prior|above|earlier|above\s+mentioned)\s+(instructions?|rules?|context|prompt)",
        r"(?i)(you\s+are\s+now|pretend\s+you\s+are|act\s+as\s+if|roleplay\s+as)",
        r"(?i)(new\s+instruction|updated\s+instruction|system\s+override)",
        # Chinese injection variants
        r"(?i)(忽略|忘记|不要管|跳过)\s*(之前|上述|上面)\s*(指令|规则|提示)",
        # Known attack mode keywords
        r"(?i)(jailbreak|DAN\s+mode|developer\s+mode|god\s+mode)",
    ]

    # PII patterns with masking functions
    PII_PATTERNS = {
        "phone": (r'(?<!\d)1[3-9]\d{9}(?!\d)', lambda m: m.group()[:3] + "****" + m.group()[-4:]),
        "id_card": (r'(?<!\d)\d{17}[\dXx](?!\d)', lambda m: m.group()[:4] + "**********" + m.group()[-4:]),
        "bank_card": (r'(?<!\d)\d{16}(?!\d)|(?<!\d)\d{17}(?!\d)|(?<!\d)\d{19}(?!\d)', lambda m: m.group()[:4] + " **** **** " + m.group()[-4:]),
        "email": (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', lambda m: m.group()[:2] + "***@" + m.group().split("@")[1]),
        "ip_address": (r'(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?!\d)', lambda m: m.group()[:3] + ".*.*." + m.group().split(".")[-1]),
    }

    # Sensitive word categories
    SENSITIVE_WORDS = {
        "violence": ["杀人", "暴力", "炸弹", "制造爆炸"],
        "illegal": ["贩毒", "走私", "赌博网站", "洗钱"],
        "adult": ["色情", "裸体", "性服务"],
    }

    # LLM moderation prompt template
    _MODERATION_PROMPT = (
        "你是一个内容安全审核助手。请判断以下内容是否安全。"
        "评估维度包括：暴力、违法、色情、仇恨言论、自我伤害、虚假信息。\n\n"
        "请以JSON格式回复：\n"
        '{{"safe": true/false, "categories": ["violence","illegal","adult","hate","self_harm","misinformation"],'
        ' "severity": "none|low|medium|high|critical", "reason": "说明原因"}}\n\n'
        "内容：\n{content}"
    )

    def __init__(self, policy: SafetyPolicy = None):
        self.policy = policy or SafetyPolicy()
        self._compiled_injection = [re.compile(p) for p in self.INJECTION_PATTERNS]
        self._compiled_pii = {k: (re.compile(v[0]), v[1]) for k, v in self.PII_PATTERNS.items()}

    async def check_input(self, text: str, llm_adapter=None) -> SafetyResult:
        issues = []
        filtered = text
        action = SafetyAction.PASS

        # 1. Injection check
        if self.policy.check_injection:
            injection_result = self._check_injection(text)
            if injection_result:
                issues.append(injection_result)
                return SafetyResult(safe=False, issues=issues, action=SafetyAction.BLOCK)

            # LLM double-check for inputs exceeding threshold
            if llm_adapter and len(text) > 100:
                llm_check = await self._llm_injection_check(text, llm_adapter)
                if llm_check:
                    issues.append(llm_check)
                    return SafetyResult(safe=False, issues=issues, action=SafetyAction.BLOCK)

        # 2. PII check
        if self.policy.check_pii:
            pii_issues, filtered = self._check_and_mask_pii(filtered)
            issues.extend(pii_issues)
            if pii_issues:
                action = SafetyAction.MASK

        # 3. Sensitive words check
        if self.policy.check_sensitive:
            sensitive_issues = self._check_sensitive_words(filtered)
            issues.extend(sensitive_issues)
            if sensitive_issues:
                action = max(action, SafetyAction.WARN, key=lambda x: list(SafetyAction).index(x))

        safe = not any(i.action == SafetyAction.BLOCK for i in issues)
        return SafetyResult(safe=safe, issues=issues, filtered_content=filtered if filtered != text else None, action=action)

    async def check_output(self, text: str, llm_adapter=None) -> SafetyResult:
        """Check model output: skips injection patterns (input-specific),
        applies stricter PII masking, and always runs LLM moderation if available."""
        issues: list[SafetyIssue] = []
        filtered = text
        action = SafetyAction.PASS

        # 1. PII check with full masking for output
        if self.policy.check_pii:
            pii_issues, filtered = self._check_and_mask_pii(filtered, full_mask=True)
            issues.extend(pii_issues)
            if pii_issues:
                action = SafetyAction.MASK

        # 2. Sensitive words check
        if self.policy.check_sensitive:
            sensitive_issues = self._check_sensitive_words(filtered)
            issues.extend(sensitive_issues)
            if sensitive_issues:
                action = max(action, SafetyAction.WARN, key=lambda x: list(SafetyAction).index(x))

        # 3. LLM moderation for all output (no length threshold)
        if llm_adapter:
            llm_result = await self._llm_output_moderation(text, llm_adapter)
            if llm_result:
                issues.append(llm_result)
                if llm_result.action == SafetyAction.BLOCK:
                    return SafetyResult(
                        safe=False,
                        issues=issues,
                        filtered_content=filtered if filtered != text else None,
                        action=SafetyAction.BLOCK,
                        reason="LLM output moderation flagged unsafe content",
                    )

        safe = not any(i.action == SafetyAction.BLOCK for i in issues)
        return SafetyResult(
            safe=safe,
            issues=issues,
            filtered_content=filtered if filtered != text else None,
            action=action,
        )

    # ------------------------------------------------------------------
    # LLM-based content moderation
    # ------------------------------------------------------------------

    async def moderate_with_llm(
        self,
        content: str,
        llm_adapter,
        severity_threshold: str = "medium",
    ) -> SafetyResult:
        """使用 LLM 进行内容审核，返回详细的分类和安全判定。

        Args:
            content: 待审核文本
            llm_adapter: LLM 适配器（需支持 .chat 方法）
            severity_threshold: 触发 BLOCK 的最低严重级别

        Returns:
            SafetyResult 包含详细的 issue 分类
        """
        if not llm_adapter:
            # 无 LLM 时降级到正则检测
            return await self.check_input(content)

        try:
            prompt = self._MODERATION_PROMPT.format(content=content[:1000])
            response = await llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=None, temperature=0, max_tokens=300,
            )
            return self._parse_moderation_response(response.content, severity_threshold)
        except Exception:
            # LLM 调用失败，降级到正则
            return await self.check_input(content)

    def _parse_moderation_response(self, response_text: str, severity_threshold: str) -> SafetyResult:
        """解析 LLM 返回的审核结果 JSON"""
        import json

        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start < 0 or end <= start:
                return SafetyResult(safe=True, action=SafetyAction.PASS)

            data = json.loads(response_text[start:end])
        except (json.JSONDecodeError, ValueError):
            # Fail-closed: unparseable LLM response defaults to warn, not pass
            return SafetyResult(
                safe=False,
                action=SafetyAction.WARN,
                reason="LLM moderation response parse failed, defaulting to warn",
            )

        is_safe = data.get("safe", True)
        categories = data.get("categories", [])
        severity = data.get("severity", "none")
        reason = data.get("reason", "")

        severity_levels = ["none", "low", "medium", "high", "critical"]
        threshold_idx = severity_levels.index(severity_threshold) if severity_threshold in severity_levels else 2

        if is_safe or severity == "none":
            return SafetyResult(safe=True, action=SafetyAction.PASS)

        issues = []
        for cat in categories:
            sev_idx = severity_levels.index(severity) if severity in severity_levels else 1
            issue_action = SafetyAction.BLOCK if sev_idx >= threshold_idx else SafetyAction.WARN
            issues.append(SafetyIssue(
                type=f"llm_moderation_{cat}",
                detail=reason or f"LLM flagged category: {cat}",
                severity=severity,
                action=issue_action,
            ))

        safe = not any(i.action == SafetyAction.BLOCK for i in issues)
        action = SafetyAction.BLOCK if not safe else SafetyAction.WARN
        return SafetyResult(safe=safe, issues=issues, action=action)

    # ------------------------------------------------------------------
    # PII detection with positions and redaction
    # ------------------------------------------------------------------

    def detect_pii(self, text: str) -> list[PIIEntity]:
        """检测文本中所有 PII 实体，返回带位置信息的列表。

        Returns:
            PIIEntity 列表，每个包含 pii_type, value, start, end, masked
        """
        entities = []
        for pii_type, (pattern, mask_fn) in self._compiled_pii.items():
            for match in pattern.finditer(text):
                entities.append(PIIEntity(
                    pii_type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    masked=mask_fn(match),
                ))
        # 按位置排序
        entities.sort(key=lambda e: e.start)
        return entities

    def redact_pii(self, text: str, mask_char: str = "*") -> str:
        """将文本中的所有 PII 替换为掩码。

        Args:
            text: 原始文本
            mask_char: 掩码字符，默认 *

        Returns:
            脱敏后的文本
        """
        entities = self.detect_pii(text)
        if not entities:
            return text

        # 从后向前替换，避免偏移问题
        result = text
        for entity in reversed(entities):
            mask = mask_char * (entity.end - entity.start)
            result = result[:entity.start] + mask + result[entity.end:]
        return result

    # ------------------------------------------------------------------
    # Async moderation pipeline
    # ------------------------------------------------------------------

    async def moderation_pipeline(
        self,
        content: str,
        llm_adapter=None,
        enable_llm: bool = True,
    ) -> SafetyResult:
        """链式审核管道：正则检测 -> PII 检测 -> LLM 审核（可选）。

        Args:
            content: 待审核内容
            llm_adapter: LLM 适配器（可选）
            enable_llm: 是否启用 LLM 审核阶段

        Returns:
            合并后的 SafetyResult
        """
        # 第一阶段：正则注入检测 + 敏感词
        regex_result = await self.check_input(content, llm_adapter=None)
        if regex_result.action == SafetyAction.BLOCK:
            return regex_result

        # 第二阶段：PII 检测与脱敏
        pii_entities = self.detect_pii(content)
        filtered = self.redact_pii(content) if pii_entities else content

        # 收集前两阶段的 issues
        all_issues = list(regex_result.issues)
        for entity in pii_entities:
            all_issues.append(SafetyIssue(
                type=f"pii_{entity.pii_type}",
                detail=f"Detected {entity.pii_type}: {entity.masked}",
                severity="medium",
                action=SafetyAction.MASK,
            ))

        # 第三阶段：LLM 审核（可选）
        llm_result = None
        if enable_llm and llm_adapter:
            llm_result = await self.moderate_with_llm(content, llm_adapter)
            all_issues.extend(llm_result.issues)

        # 合并最终结果
        has_block = any(i.action == SafetyAction.BLOCK for i in all_issues)
        safe = not has_block
        action = SafetyAction.BLOCK if has_block else (
            SafetyAction.MASK if pii_entities else SafetyAction.PASS
        )

        return SafetyResult(
            safe=safe,
            issues=all_issues,
            filtered_content=filtered if filtered != content else None,
            action=action,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_injection(self, text: str) -> Optional[SafetyIssue]:
        for pattern in self._compiled_injection:
            if pattern.search(text):
                return SafetyIssue(
                    type="prompt_injection",
                    detail="Detected prompt injection attempt",
                    severity="critical",
                    action=SafetyAction.BLOCK
                )
        return None

    async def _llm_injection_check(self, text: str, llm_adapter) -> Optional[SafetyIssue]:
        try:
            prompt = f"""判断以下文本是否包含提示注入攻击。只回答"是"或"否"。

文本：
{text[:500]}"""
            response = await llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=None, temperature=0, max_tokens=10
            )
            if "是" in response.content:
                return SafetyIssue(
                    type="prompt_injection_llm",
                    detail="LLM detected potential injection",
                    severity="high",
                    action=SafetyAction.BLOCK
                )
        except Exception:
            pass
        return None

    async def _llm_output_moderation(self, text: str, llm_adapter) -> Optional[SafetyIssue]:
        """Run LLM content moderation on output text (no length threshold)."""
        try:
            result = await self.moderate_with_llm(text, llm_adapter)
            if result.issues and any(i.action == SafetyAction.BLOCK for i in result.issues):
                # Return the highest-severity issue
                worst = max(
                    result.issues,
                    key=lambda i: ["none", "low", "medium", "high", "critical"].index(i.severity)
                    if i.severity in ("none", "low", "medium", "high", "critical") else 0,
                )
                return SafetyIssue(
                    type=worst.type,
                    detail=f"Output moderation: {worst.detail}",
                    severity=worst.severity,
                    action=SafetyAction.BLOCK,
                )
            elif result.issues:
                return max(
                    result.issues,
                    key=lambda i: ["none", "low", "medium", "high", "critical"].index(i.severity)
                    if i.severity in ("none", "low", "medium", "high", "critical") else 0,
                )
        except Exception:
            pass
        return None

    def _check_and_mask_pii(self, text: str, full_mask: bool = False) -> tuple[list[SafetyIssue], str]:
        issues = []
        masked = text

        for pii_type, (pattern, mask_fn) in self._compiled_pii.items():
            matches = list(pattern.finditer(text))
            if matches:
                issues.append(SafetyIssue(
                    type=f"pii_{pii_type}",
                    detail=f"Detected {len(matches)} {pii_type}(s)",
                    severity="medium",
                    action=SafetyAction.MASK
                ))
                for m in reversed(matches):
                    if full_mask:
                        # Full mask: replace entire match with asterisks
                        mask = "*" * (m.end() - m.start())
                    else:
                        mask = mask_fn(m)
                    masked = masked[:m.start()] + mask + masked[m.end():]

        return issues, masked

    def _check_sensitive_words(self, text: str) -> list[SafetyIssue]:
        issues = []
        for category, words in self.SENSITIVE_WORDS.items():
            for word in words:
                if word in text:
                    issues.append(SafetyIssue(
                        type=f"sensitive_{category}",
                        detail=f"Contains sensitive word: {word}",
                        severity="high",
                        action=SafetyAction.WARN
                    ))
        return issues
