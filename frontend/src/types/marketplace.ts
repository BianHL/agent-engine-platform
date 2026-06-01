export interface MarketplaceItem {
  id: string;
  tenant_id: string;
  creator_id: string;
  asset_type: 'agent' | 'knowledge_base' | 'workflow';
  asset_id: string;
  title: string;
  summary: string;
  description: string;
  cover_image?: string;
  category: string;
  tags: string[];
  visibility: string;
  status: string;
  reject_reason?: string;
  version: number;
  avg_rating: number;
  rating_count: number;
  usage_count: number;
  clone_count: number;
  featured: boolean;
  promoted_level?: string;
  creator_name?: string;
  creator_tenant_name?: string;
  published_at?: string;
  created_at: string;
  updated_at: string;
}

export interface MarketplaceListItem {
  id: string;
  asset_type: string;
  title: string;
  summary: string;
  cover_image?: string;
  category: string;
  tags: string[];
  avg_rating: number;
  rating_count: number;
  usage_count: number;
  clone_count: number;
  featured: boolean;
  promoted_level?: string;
  creator_tenant_name?: string;
  published_at?: string;
}

export interface MarketplaceRating {
  id: string;
  item_id: string;
  user_id: string;
  score: number;
  comment?: string;
  created_at: string;
  updated_at: string;
  user_name?: string;
}

export interface MarketplaceReview {
  id: string;
  item_id: string;
  tenant_id: string;
  submitter_id: string;
  reviewer_id?: string;
  review_type: string;
  status: string;
  comment?: string;
  reviewed_at?: string;
  created_at: string;
  item_title?: string;
  submitter_name?: string;
}

export interface MarketplaceStats {
  total_items: number;
  published_items: number;
  pending_review_items: number;
  total_ratings: number;
  total_clones: number;
  total_usage: number;
  avg_rating: number;
  items_by_category: Record<string, number>;
  items_by_status: Record<string, number>;
  covered_organizations: number;
  items_by_tenant: Record<string, number>;
}

export interface MarketplaceTrends {
  period_days: number;
  daily_items: Array<{ date: string; count: number }>;
  daily_ratings: Array<{ date: string; count: number; avg_score: number }>;
  daily_clones: Array<{ date: string; count: number }>;
}

// Tool Marketplace types
export interface ToolMarketplaceItem {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: string;
  tags: string[];
  version: string;
  author: string;
  author_avatar?: string;
  icon?: string;
  homepage?: string;
  repository?: string;
  license?: string;
  install_count: number;
  avg_rating: number;
  rating_count: number;
  featured: boolean;
  verified: boolean;
  status: 'active' | 'deprecated' | 'beta';
  config_schema?: Record<string, unknown>;
  examples?: ToolExample[];
  changelog?: string;
  created_at: string;
  updated_at: string;
  installed?: boolean;
}

export interface ToolExample {
  title: string;
  description: string;
  input: Record<string, unknown>;
  expected_output?: string;
}

export interface ToolMarketplaceRating {
  id: string;
  tool_id: string;
  user_id: string;
  user_name?: string;
  score: number;
  comment?: string;
  created_at: string;
}

export const TOOL_CATEGORIES = [
  'AI',
  'Data',
  'Integration',
  'Automation',
  'Communication',
  'Storage',
  'Analytics',
  'Security',
  'Utility',
] as const;

export type ToolCategory = typeof TOOL_CATEGORIES[number];
