
// blogTypes.ts
export interface User {
  id: number;
  name: string;
  profile_pic: string | null;
  relation: string;
}

// blogTypes.ts
export interface Comment {
  id: string;
  user: User;
  text: string;
  likes: number[];
  dislikes: number[];
  created_at: string;
  replies: Comment[];
  // Add these new properties
  has_liked?: boolean;
  is_replying?: boolean; // For UI state
  reply_text?: string; // For UI state
}

export interface Milestone {
  id: string;
  title: string;
  text: string;
  photo_url: string | null;
  type: string | null;
  photo_id: number | null;
}

export interface BlogHeader {
  user: User;
  type: string;
  created_at: string;
  narrative?: string;
}

export interface BlogBody {
  body_text: string | null;
  body_type_fields: {
    target_user?: User;
    milestone?: Milestone;
    report_type?: string | null;
    report_id?: string | null;
    report_kind?: string;
    time_type?: string;
    id?: string;
    level?: string;
    location?: string;
    new_users?: number;
    date?: string;
    url?: string | null;
    contribution?: string | null;
    questionid?: number | null;
    country_id?: number | null;
    state_id?: number | null;
    district_id?: number | null;
    subdistrict_id?: number | null;
    village_id?: number | null;
    target_details?: string | null;
    failure_reason?: string | null;
    title?: string | null;
    question?: {
      id: number | null;
      text: string | null;
      rank: number | null;
    };
  };
}

export interface BlogFooter {
  likes: number[];
  relevant_count: number[];
  irrelevant_count: number[];
  shares: number[];
  comments: string[];
  has_liked: boolean;
  has_shared: boolean;
}

export interface Blog {
  id: string;
  header: BlogHeader;
  body: BlogBody;
  footer: BlogFooter;
  comments: Comment[]; // Add comments to Blog interface
}

export interface BlogsState {
  blogs: Blog[];
  loading: boolean;
  error: string | null;
}

export interface BlogsSliceState {
  blogs: {
    [key: string]: BlogsState;
  };
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

export interface LikeActionResponse {
  action: string;
}

export interface ShareActionResponse {
  action: string;
}

export interface CommentActionResponse {
  action: string;
  comment?: Comment;
  comment_id?: string;
  likes_count?: number;

}