export interface UserProfile {
  id: number;
  name: string;
  profile_pic?: string;
}

export interface Conversation {
  id: string;
  last_message: string | null;
  last_message_timestamp: string | null;
  unread_count: number;
  other_user: UserProfile;
}

export interface ChatListState {
  entities: { [id: string]: Conversation };
  ids: string[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  lastFetched: number | null;
}