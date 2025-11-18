export interface InitiationNotificationData {
  gmail: string;
  first_name: string;
  last_name: string;
  profile_picture: string;
  date_of_birth: string;
  gender: string;
  country: number;
  state: number;
  district: number;
  subdistrict: number;
  village: number;
  event_type: string;
  event_id: number;
  initiator_id: number;
}

export interface MilestoneNotificationData {
  initiator_id: number;
  milestone_id: string;
  id: number;
  user_id: number;
  title: string;
  text: string;
  created_at: string;
  delivered: boolean;
  photo_id: number | null;
  photo_url: string | null;
  type: string | null;
  profile_picture: string | null;
}

export interface ConnectionNotificationData extends InitiationNotificationData {
  id: number;
}

export interface ConnectionStatusNotificationData {
  connection_id: number;
  applicant_name: string;
  profile_picture: string | null;
  status: string;
  status_message: string;
}

export interface GroupSpeakerInvitationNotificationData {
  invitation_id: number;
  group_id: number;
  group_name: string;
  profile_picture: string;
  profile_pic_source: string;
  founder_name: string;
  status: string;
  action_required: boolean;
}

// NEW: Message Notification Data
export interface MessageNotificationData {
  conversation_id: string;
  sender_id: number;
  sender_name: string;
  message_content: string;
  message_count: number;
  conversation_count: number;
  timestamp: string;
  profile_picture?: string | null; // ADD THIS LINE - make it optional
}

type NotificationBase<T extends string, D> = {
  id: number;
  notification_type: T;
  notification_message: string;
  notification_data: D;
  notification_number: string;
  notification_freshness: boolean;
  created_at?: string;
};

export type InitiationNotification = NotificationBase<"Initiation_Notification", InitiationNotificationData>;
export type ConnectionNotification = NotificationBase<"Connection_Notification", ConnectionNotificationData>;
export type ConnectionStatusNotification = NotificationBase<"Connection_Status", ConnectionStatusNotificationData>;
export type GroupSpeakerInvitationNotification = NotificationBase<"Group_Speaker_Invitation", GroupSpeakerInvitationNotificationData>;
export type MilestoneNotification = NotificationBase<"Milestone_Notification", MilestoneNotificationData>;

// NEW: Message Notification Type
export type MessageNotification = NotificationBase<"Message_Notification", MessageNotificationData>;

export type Notification =
  | InitiationNotification
  | ConnectionNotification
  | ConnectionStatusNotification
  | GroupSpeakerInvitationNotification
  | MilestoneNotification
  | MessageNotification;