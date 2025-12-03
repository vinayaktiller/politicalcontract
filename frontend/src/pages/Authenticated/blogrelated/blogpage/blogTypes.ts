// blogTypes.ts
export interface User {
  id: number;
  name: string;
  profile_pic: string | null;
  relation: string;
}

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
  relation?: string; // Added this field
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
  comments: Comment[];
  
  // Add these missing properties that are used in your components
  is_shared?: boolean;
  shared_by_user_id?: string;
  original_author_id?: string;
  created_at?: string;
  narrative?: string;
  
  // Add any other properties that might come from the API
  type?: string;
  user?: User; // Sometimes blog might have direct user reference
}

export interface BlogsState {
  blogs: Blog[] | any; // Allow any type since your normalizeBlogs handles different shapes
  loading: boolean;
  error: string | null;
}

export interface BlogsSliceState {
  blogs: {
    [key: string]: BlogsState;
  };
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  needsRefresh: {
    [key: string]: boolean;
  };
  scrollPositions: { // NEW: Add scroll positions to state
    [key: string]: number;
  };
  myblogscrollPositions: { // NEW: Scroll positions for My Blogs
    [key: string]: number;
  };
  mainFetchDone: { // NEW: Track if main fetch has been done for each blog type
    [key: string]: boolean;
  };
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

// Add these types for better type safety
export interface FetchBlogsParams {
  blogType: string;
}

export interface LikeBlogParams {
  blogType: string;
  blogId: string;
}

export interface ShareBlogParams {
  blogType: string;
  blogId: string;
}

export interface AddCommentParams {
  blogType: string;
  blogId: string;
  text: string;
  parentCommentId?: string;
}