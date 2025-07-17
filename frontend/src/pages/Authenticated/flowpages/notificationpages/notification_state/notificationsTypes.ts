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

type NotificationBase<T extends string, D> = {
  id: number;
  notification_type: T;
  notification_message: string;
  notification_data: D;
  notification_number: number;
  notification_freshness: boolean;
  created_at?: string;
};

export type InitiationNotification = NotificationBase<"Initiation_Notification", InitiationNotificationData>;
export type ConnectionNotification = NotificationBase<"Connection_Notification", ConnectionNotificationData>;
export type ConnectionStatusNotification = NotificationBase<"Connection_Status", ConnectionStatusNotificationData>;
export type GroupSpeakerInvitationNotification = NotificationBase<"Group_Speaker_Invitation", GroupSpeakerInvitationNotificationData>;
export type Notification = InitiationNotification | ConnectionNotification | ConnectionStatusNotification | GroupSpeakerInvitationNotification;
