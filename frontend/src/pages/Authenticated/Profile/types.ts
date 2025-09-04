export interface User {
  id: number;
  gmail: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  age: number;
  gender: string;
  country: Country | null;
  state: State | null;
  district: District | null;
  subdistrict: Subdistrict | null;
  village: Village | null;
  is_online: boolean;
  date_joined: string;
}

export interface Country {
  id: number;
  name: string;
}

export interface State {
  id: number;
  name: string;
  country: Country;
}

export interface District {
  id: number;
  name: string;
  state: State;
}

export interface Subdistrict {
  id: number;
  name: string;
  district: District;
}

export interface Village {
  id: number;
  name: string;
  subdistrict: Subdistrict;
}

export interface Milestone {
  id: string;
  user_id: number;
  title: string;
  text: string;
  created_at: string;
  delivered: boolean;
  photo_id: number | null;
  photo_url: string | null;
  type: string | null;
}

export interface Group {
  id: number;
  name: string;
  founder: number;
  profile_pic: string | null;
  speakers: number[];
  members: number[];
  country: Country | null;
  state: State | null;
  district: District | null;
  subdistrict: Subdistrict | null;
  village: Village | null;
  created_at: string;
}

export interface ProfileData {
  user: User;
  user_tree: {
    id: number;
    name: string;
    profilepic: string | null;
    childcount: number;
    influence: number;
    height: number;
    weight: number;
    depth: number;
  } | null;
  profile_description: string;
  milestones: Milestone[];
  founded_groups: Group[];
  speaking_groups: Group[];
  streak: number;
}