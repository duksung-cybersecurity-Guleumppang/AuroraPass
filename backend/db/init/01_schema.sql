-- Enable extension for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- users
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username varchar(50) NOT NULL UNIQUE,
  email varchar(255) NOT NULL UNIQUE,
  password_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- courses
CREATE TABLE IF NOT EXISTS courses (
  id varchar(40) PRIMARY KEY,
  title text NOT NULL,
  capacity int NOT NULL CHECK (capacity >= 0),
  enrolled_count int NOT NULL DEFAULT 0 CHECK (enrolled_count >= 0),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- carts
CREATE TABLE IF NOT EXISTS carts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_carts_user ON carts(user_id);

-- cart_items
CREATE TABLE IF NOT EXISTS cart_items (
  cart_id uuid NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
  course_id varchar(40) NOT NULL REFERENCES courses(id),
  added_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (cart_id, course_id)
);

-- enrollments
CREATE TABLE IF NOT EXISTS enrollments (
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  course_id varchar(40) NOT NULL REFERENCES courses(id),
  status varchar(20) NOT NULL DEFAULT 'ENROLLED',
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, course_id)
);
CREATE INDEX IF NOT EXISTS ix_enrollments_course ON enrollments(course_id);


-- captcha_files
CREATE TABLE IF NOT EXISTS captcha_files (
  id varchar(40) PRIMARY KEY,
  filename varchar(255) UNIQUE NOT NULL,
  answer varchar(100) NOT NULL,
  audio_data bytea NOT NULL,
  content_type varchar(50) NOT NULL DEFAULT 'audio/wav',
  created_at timestamptz NOT NULL DEFAULT now()
);

