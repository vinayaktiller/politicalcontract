export interface ProfileData {
  id: number;
  name: string;
  profilepic: string | null;
  childcount: number;
  influence: number;
  height: number;
  weight: number;
  depth: number;
  children_count?: number;
  initiates?: RelationProfile[];
  members?: RelationProfile[];
  connections?: RelationProfile[];
  children?: ChildProfile[];
  groupmembers?: RelationProfile[]; 
  online_initiates?: RelationProfile[]; 
}

export interface RelationProfile {
  id: number;
  name: string;
  profilepic: string | null;
  childcount: number;
  influence: number;
  height: number;
  weight: number;
  depth: number;
}

export interface ChildProfile {
  id: number;
  name: string;
  profilepic: string | null;
  childcount: number;
  influence: number;
  height: number;
  weight: number;
  depth: number;
}

export interface TimelineState {
  timelineNumber: number;
  timelineOwner: number;
  timelineHead: ProfileData[];
  timelineTail: ProfileData[];
  nextPage: number | null; // 0 = not fetched, null = end
  timelineHeadLength: number;
  newload: number;
  scrollPosition: number | null;
  error?: string | null;
}

export interface TimelineSliceState {
  timelines: {
    [timelineNumber: number]: TimelineState;
  };
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

export interface TimelineHeadResponse {
  user_profile?: ProfileData;
  count: number;
  next: string | null;
  previous: string | null;
  load: number;
  results: ProfileData[];
}

export interface TimelineTailResponse extends ProfileData {
  children?: ChildProfile[];
}
