Table users {
  id             int          [pk, increment]
  name           varchar(100) [not null]
  username       varchar(50)  [not null, unique]
  email          varchar(255) [not null, unique]
  password_hash  varchar(255) [not null]
  role           varchar(30)  [not null] // admin, regular, facility_manager, moderator, auditor, service_account
  created_at     timestamptz  [not null]
}

Table rooms {
  id             int          [pk, increment]
  name           varchar(100) [not null, unique]
  capacity       int          [not null]
  equipment      text         // e.g. "projector,whiteboard,video"
  location       varchar(100) [not null]
  status         varchar(30)  [not null] // active, out_of_service, etc.
  created_at     timestamptz  [not null]
}

Table bookings {
  id             int          [pk, increment]
  user_id        int          [not null]
  room_id        int          [not null]
  start_time     timestamptz  [not null]
  end_time       timestamptz  [not null]
  status         varchar(30)  [not null] // pending, confirmed, cancelled, etc.
  created_at     timestamptz  [not null]
}

Table reviews {
  id             int          [pk, increment]
  user_id        int          [not null]
  room_id        int          [not null]
  rating         int          [not null] // 1..5
  comment        text
  flagged        bool         [not null, default: false]
  created_at     timestamptz  [not null]
  updated_at     timestamptz
}

// Relationships
Ref: bookings.user_id > users.id
Ref: bookings.room_id > rooms.id

Ref: reviews.user_id  > users.id
Ref: reviews.room_id  > rooms.id

// Suggested indexes (very useful later, especially if you pick "Database Indexing" as a Part II task)