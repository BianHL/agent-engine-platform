from fastapi import APIRouter

from app.api.v1 import (
    agents,
    audit,
    auth,
    chat,
    conversations,
    evaluations,
    feedbacks,
    data_import,
    knowledge,
    marketplace,
    memory,
    model_compare,
    models as models_router,
    multi_agent,
    publish,
    roles,
    tasks,
    tenants,
    tokens,
    tools,
    triggers,
    usage,
    users,
    variables,
    webhooks,
    workflows)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(agents.router)
api_router.include_router(knowledge.router)
api_router.include_router(models_router.router)
api_router.include_router(chat.router)
api_router.include_router(usage.router)
api_router.include_router(conversations.router)
api_router.include_router(workflows.router)
api_router.include_router(tasks.router)
api_router.include_router(tenants.router)
api_router.include_router(memory.router)
api_router.include_router(users.router)
api_router.include_router(tools.router)
api_router.include_router(feedbacks.router)
api_router.include_router(audit.router)
api_router.include_router(evaluations.router)
api_router.include_router(triggers.router)
api_router.include_router(multi_agent.router)
api_router.include_router(roles.router)
api_router.include_router(tokens.router)
api_router.include_router(webhooks.router)
api_router.include_router(marketplace.router)
api_router.include_router(data_import.router)
api_router.include_router(model_compare.router)
api_router.include_router(variables.router)
api_router.include_router(publish.router)
