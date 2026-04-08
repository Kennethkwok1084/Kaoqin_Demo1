-- 校园网部门综合运维工时平台 PostgreSQL 建表 SQL（V2）
-- 说明：
-- 1. 面向 PostgreSQL 14+ 编写
-- 2. 使用 public schema
-- 3. 状态字段尽量采用 smallint + 注释方式，避免后续频繁改 ENUM
-- 4. 如需 UUID，可先执行：CREATE EXTENSION IF NOT EXISTS pgcrypto;

BEGIN;

CREATE TABLE IF NOT EXISTS app_user (
    id                  BIGSERIAL PRIMARY KEY,
    student_no          VARCHAR(32) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    real_name           VARCHAR(64) NOT NULL,
    role_code           VARCHAR(16) NOT NULL DEFAULT 'user',
    phone               VARCHAR(32),
    email               VARCHAR(128),
    avatar_url          TEXT,
    status              SMALLINT NOT NULL DEFAULT 1,
    last_login_at       TIMESTAMPTZ,
    remark              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_app_user_role_code CHECK (role_code IN ('admin','user')),
    CONSTRAINT ck_app_user_status CHECK (status IN (0,1,2))
);
COMMENT ON TABLE app_user IS '系统用户表，管理员和普通用户统一存储';
COMMENT ON COLUMN app_user.status IS '0禁用 1启用 2锁定';

CREATE INDEX IF NOT EXISTS idx_app_user_role_status ON app_user(role_code, status);

CREATE TABLE IF NOT EXISTS user_profile (
    user_id             BIGINT PRIMARY KEY REFERENCES app_user(id) ON DELETE CASCADE,
    nickname            VARCHAR(64),
    gender              SMALLINT,
    department_name     VARCHAR(128),
    grade_name          VARCHAR(64),
    class_name          VARCHAR(64),
    major_name          VARCHAR(128),
    id_card_mask        VARCHAR(32),
    emergency_contact   VARCHAR(64),
    emergency_phone     VARCHAR(32),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_user_profile_gender CHECK (gender IN (0,1,2) OR gender IS NULL)
);
COMMENT ON TABLE user_profile IS '用户扩展资料表';

CREATE TABLE IF NOT EXISTS auth_refresh_token (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    refresh_token       VARCHAR(255) NOT NULL UNIQUE,
    device_id           VARCHAR(128),
    device_name         VARCHAR(128),
    platform_code       VARCHAR(32),
    expires_at          TIMESTAMPTZ NOT NULL,
    revoked_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE auth_refresh_token IS '登录刷新令牌表';

CREATE INDEX IF NOT EXISTS idx_refresh_token_user ON auth_refresh_token(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_token_expires ON auth_refresh_token(expires_at);

CREATE TABLE IF NOT EXISTS sys_config (
    id                  BIGSERIAL PRIMARY KEY,
    config_group        VARCHAR(64) NOT NULL,
    config_key          VARCHAR(128) NOT NULL,
    config_value        JSONB NOT NULL DEFAULT '{}'::jsonb,
    description         TEXT,
    is_enabled          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(config_group, config_key)
);
COMMENT ON TABLE sys_config IS '系统配置表，存放异常阈值、签到半径、二维码刷新时间等';

CREATE TABLE IF NOT EXISTS building (
    id                  BIGSERIAL PRIMARY KEY,
    building_code       VARCHAR(32) NOT NULL UNIQUE,
    building_name       VARCHAR(128) NOT NULL,
    campus_name         VARCHAR(128),
    area_name           VARCHAR(128),
    longitude           NUMERIC(10,6),
    latitude            NUMERIC(10,6),
    status              SMALLINT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_building_status CHECK (status IN (0,1))
);
COMMENT ON TABLE building IS '宿舍楼栋基础表';

CREATE TABLE IF NOT EXISTS dorm_room (
    id                  BIGSERIAL PRIMARY KEY,
    building_id         BIGINT NOT NULL REFERENCES building(id) ON DELETE RESTRICT,
    room_no             VARCHAR(32) NOT NULL,
    floor_no            VARCHAR(16),
    target_ssid         VARCHAR(64) NOT NULL DEFAULT 'GCC',
    target_bssid        VARCHAR(64) NOT NULL,
    dorm_label          VARCHAR(128),
    active_repair_weight INTEGER NOT NULL DEFAULT 0,
    last_sampled_at     TIMESTAMPTZ,
    status              SMALLINT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(building_id, room_no),
    CONSTRAINT ck_dorm_room_status CHECK (status IN (0,1))
);
COMMENT ON TABLE dorm_room IS '宿舍基础表，存放目标SSID和BSSID';
COMMENT ON COLUMN dorm_room.active_repair_weight IS '当前月周期内报修权重，用于抽检加权随机';

CREATE INDEX IF NOT EXISTS idx_dorm_room_building_status ON dorm_room(building_id, status);
CREATE INDEX IF NOT EXISTS idx_dorm_room_last_sampled ON dorm_room(last_sampled_at);

CREATE TABLE IF NOT EXISTS media_file (
    id                  BIGSERIAL PRIMARY KEY,
    biz_type            VARCHAR(32) NOT NULL,
    biz_id              BIGINT NOT NULL,
    file_type           VARCHAR(16) NOT NULL,
    storage_path        TEXT NOT NULL,
    file_name           VARCHAR(255) NOT NULL,
    content_type        VARCHAR(128),
    file_size           BIGINT NOT NULL DEFAULT 0,
    sha256_hex          VARCHAR(128),
    watermark_payload   JSONB,
    uploaded_by         BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_media_file_type CHECK (file_type IN ('image','video','audio','ocr_source','other'))
);
COMMENT ON TABLE media_file IS '统一媒体文件表，支持图片、视频、OCR原图等';

CREATE INDEX IF NOT EXISTS idx_media_file_biz ON media_file(biz_type, biz_id);

CREATE TABLE IF NOT EXISTS task_coop (
    id                  BIGSERIAL PRIMARY KEY,
    task_code           VARCHAR(64) NOT NULL UNIQUE,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    location_text       VARCHAR(255),
    building_id         BIGINT REFERENCES building(id) ON DELETE SET NULL,
    signup_need_review  BOOLEAN NOT NULL DEFAULT FALSE,
    sign_in_mode_mask   INTEGER NOT NULL DEFAULT 0,
    no_show_enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    status              SMALLINT NOT NULL DEFAULT 0,
    created_by          BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    published_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_task_coop_status CHECK (status IN (0,1,2,3,4,5))
);
COMMENT ON TABLE task_coop IS '协助任务主表';
COMMENT ON COLUMN task_coop.sign_in_mode_mask IS '签到方式位掩码：1定位 2扫码 4用户签到 8管理员确认 16签到后复核';
COMMENT ON COLUMN task_coop.status IS '0草稿 1已发布 2执行中 3待审核 4已完成 5已关闭';

CREATE INDEX IF NOT EXISTS idx_task_coop_status_time ON task_coop(status, published_at DESC);

CREATE TABLE IF NOT EXISTS task_coop_slot (
    id                  BIGSERIAL PRIMARY KEY,
    coop_task_id        BIGINT NOT NULL REFERENCES task_coop(id) ON DELETE CASCADE,
    slot_title          VARCHAR(128),
    start_time          TIMESTAMPTZ NOT NULL,
    end_time            TIMESTAMPTZ NOT NULL,
    signup_limit        INTEGER NOT NULL DEFAULT 1,
    sort_no             INTEGER NOT NULL DEFAULT 1,
    status              SMALLINT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_task_coop_slot_time CHECK (end_time > start_time),
    CONSTRAINT ck_task_coop_slot_status CHECK (status IN (0,1))
);
COMMENT ON TABLE task_coop_slot IS '协助任务时间段表，允许一个任务配置多个时间段';

CREATE INDEX IF NOT EXISTS idx_task_coop_slot_task ON task_coop_slot(coop_task_id, start_time);

CREATE TABLE IF NOT EXISTS task_coop_signup (
    id                  BIGSERIAL PRIMARY KEY,
    coop_task_id        BIGINT NOT NULL REFERENCES task_coop(id) ON DELETE CASCADE,
    coop_slot_id        BIGINT NOT NULL REFERENCES task_coop_slot(id) ON DELETE CASCADE,
    user_id             BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    signup_source       VARCHAR(16) NOT NULL DEFAULT 'self',
    status              SMALLINT NOT NULL DEFAULT 1,
    reviewed_by         BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    reviewed_at         TIMESTAMPTZ,
    cancel_reason       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(coop_slot_id, user_id),
    CONSTRAINT ck_task_coop_signup_source CHECK (signup_source IN ('self','assign')),
    CONSTRAINT ck_task_coop_signup_status CHECK (status IN (0,1,2,3,4))
);
COMMENT ON TABLE task_coop_signup IS '协助任务报名表';
COMMENT ON COLUMN task_coop_signup.status IS '0已取消 1已报名 2待审核 3已拒绝 4已爽约';

CREATE INDEX IF NOT EXISTS idx_task_coop_signup_user ON task_coop_signup(user_id, status);

CREATE TABLE IF NOT EXISTS task_coop_attendance (
    id                  BIGSERIAL PRIMARY KEY,
    coop_signup_id      BIGINT NOT NULL REFERENCES task_coop_signup(id) ON DELETE CASCADE,
    sign_in_at          TIMESTAMPTZ,
    sign_out_at         TIMESTAMPTZ,
    sign_in_type        VARCHAR(16),
    sign_out_type       VARCHAR(16),
    sign_in_longitude   NUMERIC(10,6),
    sign_in_latitude    NUMERIC(10,6),
    sign_out_longitude  NUMERIC(10,6),
    sign_out_latitude   NUMERIC(10,6),
    qr_token            VARCHAR(128),
    admin_confirmed_by  BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    admin_confirmed_at  TIMESTAMPTZ,
    duration_minutes    INTEGER NOT NULL DEFAULT 0,
    review_status       SMALLINT NOT NULL DEFAULT 0,
    remark              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_task_coop_attendance_type CHECK (
        sign_in_type IN ('gps','qr','manual','admin','hybrid') OR sign_in_type IS NULL
    ),
    CONSTRAINT ck_task_coop_attendance_review CHECK (review_status IN (0,1,2))
);
COMMENT ON TABLE task_coop_attendance IS '协助任务签到签退记录表';

CREATE INDEX IF NOT EXISTS idx_task_coop_attendance_signup ON task_coop_attendance(coop_signup_id);

CREATE TABLE IF NOT EXISTS task_inspection (
    id                  BIGSERIAL PRIMARY KEY,
    task_code           VARCHAR(64) NOT NULL UNIQUE,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    building_id         BIGINT REFERENCES building(id) ON DELETE SET NULL,
    planned_start_at    TIMESTAMPTZ,
    planned_end_at      TIMESTAMPTZ,
    assigned_by         BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    status              SMALLINT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_task_inspection_status CHECK (status IN (0,1,2,3,4,5))
);
COMMENT ON TABLE task_inspection IS '巡检任务主表';

CREATE TABLE IF NOT EXISTS task_inspection_user (
    id                  BIGSERIAL PRIMARY KEY,
    inspection_task_id  BIGINT NOT NULL REFERENCES task_inspection(id) ON DELETE CASCADE,
    user_id             BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    role_in_task        VARCHAR(16) NOT NULL DEFAULT 'executor',
    status              SMALLINT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(inspection_task_id, user_id),
    CONSTRAINT ck_task_inspection_user_role CHECK (role_in_task IN ('leader','executor')),
    CONSTRAINT ck_task_inspection_user_status CHECK (status IN (0,1))
);
COMMENT ON TABLE task_inspection_user IS '巡检任务参与人员表';

CREATE TABLE IF NOT EXISTS task_inspection_point (
    id                  BIGSERIAL PRIMARY KEY,
    inspection_task_id  BIGINT NOT NULL REFERENCES task_inspection(id) ON DELETE CASCADE,
    cabinet_name        VARCHAR(128) NOT NULL,
    cabinet_location    VARCHAR(255),
    sort_no             INTEGER NOT NULL DEFAULT 1,
    is_mandatory_photo  BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE task_inspection_point IS '巡检点位/机柜表';

CREATE INDEX IF NOT EXISTS idx_task_inspection_point_task ON task_inspection_point(inspection_task_id, sort_no);

CREATE TABLE IF NOT EXISTS inspection_record (
    id                  BIGSERIAL PRIMARY KEY,
    inspection_task_id  BIGINT NOT NULL REFERENCES task_inspection(id) ON DELETE CASCADE,
    inspection_point_id BIGINT NOT NULL REFERENCES task_inspection_point(id) ON DELETE CASCADE,
    user_id             BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    result_status       SMALLINT NOT NULL DEFAULT 1,
    exception_type      VARCHAR(64),
    exception_desc      TEXT,
    handled_desc        TEXT,
    media_image_id      BIGINT REFERENCES media_file(id) ON DELETE SET NULL,
    media_video_id      BIGINT REFERENCES media_file(id) ON DELETE SET NULL,
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_by         BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    reviewed_at         TIMESTAMPTZ,
    review_status       SMALLINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(inspection_task_id, inspection_point_id, user_id),
    CONSTRAINT ck_inspection_record_result CHECK (result_status IN (1,2,3)),
    CONSTRAINT ck_inspection_record_review CHECK (review_status IN (0,1,2))
);
COMMENT ON TABLE inspection_record IS '巡检记录表，按机柜逐条提交';
COMMENT ON COLUMN inspection_record.result_status IS '1正常 2异常 3已处理';

CREATE TABLE IF NOT EXISTS task_sampling (
    id                  BIGSERIAL PRIMARY KEY,
    task_code           VARCHAR(64) NOT NULL UNIQUE,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    building_id         BIGINT NOT NULL REFERENCES building(id) ON DELETE RESTRICT,
    target_room_count   INTEGER NOT NULL,
    sample_strategy     VARCHAR(32) NOT NULL DEFAULT 'weighted_random',
    exclude_days        INTEGER NOT NULL DEFAULT 30,
    assigned_by         BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    planned_start_at    TIMESTAMPTZ,
    planned_end_at      TIMESTAMPTZ,
    status              SMALLINT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_task_sampling_strategy CHECK (sample_strategy IN ('weighted_random')),
    CONSTRAINT ck_task_sampling_status CHECK (status IN (0,1,2,3,4,5))
);
COMMENT ON TABLE task_sampling IS '网络抽检任务主表';

CREATE TABLE IF NOT EXISTS task_sampling_user (
    id                  BIGSERIAL PRIMARY KEY,
    sampling_task_id    BIGINT NOT NULL REFERENCES task_sampling(id) ON DELETE CASCADE,
    user_id             BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    role_in_task        VARCHAR(16) NOT NULL DEFAULT 'executor',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(sampling_task_id, user_id),
    CONSTRAINT ck_task_sampling_user_role CHECK (role_in_task IN ('leader','executor'))
);
COMMENT ON TABLE task_sampling_user IS '抽检任务参与人员表';

CREATE TABLE IF NOT EXISTS task_sampling_room (
    id                  BIGSERIAL PRIMARY KEY,
    sampling_task_id    BIGINT NOT NULL REFERENCES task_sampling(id) ON DELETE CASCADE,
    dorm_room_id        BIGINT NOT NULL REFERENCES dorm_room(id) ON DELETE RESTRICT,
    generated_weight    INTEGER NOT NULL DEFAULT 0,
    is_completed        BOOLEAN NOT NULL DEFAULT FALSE,
    completed_by        BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(sampling_task_id, dorm_room_id)
);
COMMENT ON TABLE task_sampling_room IS '抽检任务生成后的宿舍清单';

CREATE INDEX IF NOT EXISTS idx_task_sampling_room_task ON task_sampling_room(sampling_task_id, is_completed);

CREATE TABLE IF NOT EXISTS sampling_record (
    id                      BIGSERIAL PRIMARY KEY,
    sampling_task_id        BIGINT NOT NULL REFERENCES task_sampling(id) ON DELETE CASCADE,
    sampling_task_room_id   BIGINT NOT NULL REFERENCES task_sampling_room(id) ON DELETE CASCADE,
    dorm_room_id            BIGINT NOT NULL REFERENCES dorm_room(id) ON DELETE RESTRICT,
    user_id                 BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    detect_mode             VARCHAR(16) NOT NULL DEFAULT 'full',
    current_ssid            VARCHAR(64),
    current_bssid           VARCHAR(64),
    bssid_match             BOOLEAN,
    ipv4_addr               VARCHAR(64),
    gateway_addr            VARCHAR(64),
    dns_list                JSONB,
    operator_name           VARCHAR(64),
    channel_no              INTEGER,
    negotiated_rate_mbps    NUMERIC(10,2),
    signal_strength_dbm     INTEGER,
    loss_rate_pct           NUMERIC(5,2),
    intranet_ping_ms        NUMERIC(10,2),
    internet_ping_ms        NUMERIC(10,2),
    udp_jitter_ms           NUMERIC(10,2),
    udp_loss_rate_pct       NUMERIC(5,2),
    tcp_rtt_ms              NUMERIC(10,2),
    down_speed_mbps         NUMERIC(10,2),
    up_speed_mbps           NUMERIC(10,2),
    interference_score      NUMERIC(10,2),
    exception_auto          BOOLEAN NOT NULL DEFAULT FALSE,
    exception_manual        BOOLEAN NOT NULL DEFAULT FALSE,
    manual_exception_note   TEXT,
    review_status           SMALLINT NOT NULL DEFAULT 0,
    reviewed_by             BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    reviewed_at             TIMESTAMPTZ,
    started_at              TIMESTAMPTZ,
    finished_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_sampling_record_mode CHECK (detect_mode IN ('full','single_item')),
    CONSTRAINT ck_sampling_record_review CHECK (review_status IN (0,1,2))
);
COMMENT ON TABLE sampling_record IS '网络抽检结果主表';

CREATE INDEX IF NOT EXISTS idx_sampling_record_task_user ON sampling_record(sampling_task_id, user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sampling_record_room ON sampling_record(dorm_room_id, created_at DESC);

CREATE TABLE IF NOT EXISTS sampling_scan_detail (
    id                  BIGSERIAL PRIMARY KEY,
    sampling_record_id  BIGINT NOT NULL REFERENCES sampling_record(id) ON DELETE CASCADE,
    ssid                VARCHAR(128),
    bssid               VARCHAR(64),
    channel_no          INTEGER,
    signal_strength_dbm INTEGER,
    is_same_channel     BOOLEAN NOT NULL DEFAULT FALSE,
    is_adjacent_channel BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE sampling_scan_detail IS '周边SSID/BSSID扫描明细表';

CREATE INDEX IF NOT EXISTS idx_sampling_scan_detail_record ON sampling_scan_detail(sampling_record_id);

CREATE TABLE IF NOT EXISTS sampling_test_detail (
    id                  BIGSERIAL PRIMARY KEY,
    sampling_record_id  BIGINT NOT NULL REFERENCES sampling_record(id) ON DELETE CASCADE,
    item_code           VARCHAR(32) NOT NULL,
    target_host         VARCHAR(255),
    result_payload      JSONB NOT NULL DEFAULT '{}'::jsonb,
    save_to_record      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE sampling_test_detail IS '单项目检测明细表，例如iperf3或单独测速结果';

CREATE TABLE IF NOT EXISTS repair_ticket (
    id                      BIGSERIAL PRIMARY KEY,
    repair_no               VARCHAR(64),
    ticket_source           VARCHAR(16) NOT NULL,
    title                   VARCHAR(255),
    report_user_name        VARCHAR(64),
    report_phone            VARCHAR(32),
    building_id             BIGINT REFERENCES building(id) ON DELETE SET NULL,
    dorm_room_id            BIGINT REFERENCES dorm_room(id) ON DELETE SET NULL,
    issue_content           TEXT,
    issue_category          VARCHAR(64),
    solution_desc           TEXT,
    solve_status            SMALLINT NOT NULL DEFAULT 0,
    source_screenshot_id    BIGINT REFERENCES media_file(id) ON DELETE SET NULL,
    doorplate_image_id      BIGINT REFERENCES media_file(id) ON DELETE SET NULL,
    ocr_payload             JSONB,
    match_status            SMALLINT NOT NULL DEFAULT 0,
    matched_import_row_id   BIGINT,
    created_by              BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_repair_ticket_source CHECK (ticket_source IN ('online','offline')),
    CONSTRAINT ck_repair_ticket_solve_status CHECK (solve_status IN (0,1,2)),
    CONSTRAINT ck_repair_ticket_match_status CHECK (match_status IN (0,1,2,3))
);
COMMENT ON TABLE repair_ticket IS '报修单表，兼容线上单和线下单';
COMMENT ON COLUMN repair_ticket.solve_status IS '0未处理 1处理中 2已解决';
COMMENT ON COLUMN repair_ticket.match_status IS '0未匹配 1用户已提交匹配 2审核通过 3审核驳回';

CREATE INDEX IF NOT EXISTS idx_repair_ticket_no ON repair_ticket(repair_no);
CREATE INDEX IF NOT EXISTS idx_repair_ticket_source_status ON repair_ticket(ticket_source, match_status, created_at DESC);

CREATE TABLE IF NOT EXISTS repair_ticket_member (
    id                  BIGSERIAL PRIMARY KEY,
    repair_ticket_id    BIGINT NOT NULL REFERENCES repair_ticket(id) ON DELETE CASCADE,
    user_id             BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    member_role         VARCHAR(16) NOT NULL DEFAULT 'assist',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(repair_ticket_id, user_id),
    CONSTRAINT ck_repair_ticket_member_role CHECK (member_role IN ('primary','assist'))
);
COMMENT ON TABLE repair_ticket_member IS '报修单参与人表，多人参与时每人都可获得完整工时';

CREATE TABLE IF NOT EXISTS import_batch (
    id                  BIGSERIAL PRIMARY KEY,
    batch_type          VARCHAR(32) NOT NULL,
    file_name           VARCHAR(255) NOT NULL,
    file_storage_path   TEXT,
    imported_by         BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    total_rows          INTEGER NOT NULL DEFAULT 0,
    success_rows        INTEGER NOT NULL DEFAULT 0,
    failed_rows         INTEGER NOT NULL DEFAULT 0,
    status              SMALLINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at         TIMESTAMPTZ,
    CONSTRAINT ck_import_batch_type CHECK (batch_type IN ('repair_total','repair_legacy','other')),
    CONSTRAINT ck_import_batch_status CHECK (status IN (0,1,2,3))
);
COMMENT ON TABLE import_batch IS '导入批次表';

CREATE TABLE IF NOT EXISTS import_repair_row (
    id                  BIGSERIAL PRIMARY KEY,
    import_batch_id      BIGINT NOT NULL REFERENCES import_batch(id) ON DELETE CASCADE,
    repair_no           VARCHAR(64),
    report_user_name    VARCHAR(64),
    report_phone        VARCHAR(32),
    building_name       VARCHAR(128),
    room_no             VARCHAR(32),
    issue_content       TEXT,
    raw_payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
    matched_ticket_id   BIGINT REFERENCES repair_ticket(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE import_repair_row IS '报修总表导入明细';

CREATE INDEX IF NOT EXISTS idx_import_repair_row_no ON import_repair_row(repair_no);
CREATE INDEX IF NOT EXISTS idx_import_repair_row_match ON import_repair_row(matched_ticket_id);

CREATE TABLE IF NOT EXISTS repair_match_application (
    id                  BIGSERIAL PRIMARY KEY,
    repair_ticket_id    BIGINT NOT NULL REFERENCES repair_ticket(id) ON DELETE CASCADE,
    import_repair_row_id BIGINT NOT NULL REFERENCES import_repair_row(id) ON DELETE CASCADE,
    applied_by          BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    apply_note          TEXT,
    status              SMALLINT NOT NULL DEFAULT 0,
    reviewed_by         BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    reviewed_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(repair_ticket_id),
    CONSTRAINT ck_repair_match_application_status CHECK (status IN (0,1,2))
);
COMMENT ON TABLE repair_match_application IS '用户提交的报修匹配申请';

CREATE TABLE IF NOT EXISTS workhour_rule (
    id                  BIGSERIAL PRIMARY KEY,
    rule_code           VARCHAR(64) NOT NULL UNIQUE,
    rule_name           VARCHAR(128) NOT NULL,
    biz_type            VARCHAR(32) NOT NULL,
    formula_desc        TEXT NOT NULL,
    formula_json        JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_enabled          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_workhour_rule_biz CHECK (biz_type IN ('coop','inspection','sampling','repair'))
);
COMMENT ON TABLE workhour_rule IS '工时规则表';

CREATE TABLE IF NOT EXISTS workhour_tag (
    id                  BIGSERIAL PRIMARY KEY,
    tag_code            VARCHAR(64) NOT NULL UNIQUE,
    tag_name            VARCHAR(128) NOT NULL,
    tag_type            VARCHAR(32) NOT NULL,
    bonus_mode          VARCHAR(16) NOT NULL DEFAULT 'add',
    bonus_value         NUMERIC(10,2) NOT NULL DEFAULT 0,
    is_enabled          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_workhour_tag_type CHECK (tag_type IN ('good_review','burst_order','custom')),
    CONSTRAINT ck_workhour_tag_bonus_mode CHECK (bonus_mode IN ('add','multiply'))
);
COMMENT ON TABLE workhour_tag IS '工时标签表，兼容爆单、好评单等规则';

CREATE TABLE IF NOT EXISTS workhour_entry (
    id                  BIGSERIAL PRIMARY KEY,
    biz_type            VARCHAR(32) NOT NULL,
    biz_id              BIGINT NOT NULL,
    user_id             BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    source_rule_id      BIGINT REFERENCES workhour_rule(id) ON DELETE SET NULL,
    base_minutes        INTEGER NOT NULL DEFAULT 0,
    final_minutes       INTEGER NOT NULL DEFAULT 0,
    review_status       SMALLINT NOT NULL DEFAULT 0,
    reviewed_by         BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    reviewed_at         TIMESTAMPTZ,
    review_note         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_workhour_entry_biz CHECK (biz_type IN ('coop','inspection','sampling','repair')),
    CONSTRAINT ck_workhour_entry_review CHECK (review_status IN (0,1,2))
);
COMMENT ON TABLE workhour_entry IS '工时明细表，自动计算后待管理员审核';

CREATE INDEX IF NOT EXISTS idx_workhour_entry_user_time ON workhour_entry(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workhour_entry_biz ON workhour_entry(biz_type, biz_id);

CREATE TABLE IF NOT EXISTS workhour_entry_tag (
    id                  BIGSERIAL PRIMARY KEY,
    workhour_entry_id   BIGINT NOT NULL REFERENCES workhour_entry(id) ON DELETE CASCADE,
    workhour_tag_id     BIGINT NOT NULL REFERENCES workhour_tag(id) ON DELETE RESTRICT,
    bonus_minutes       INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(workhour_entry_id, workhour_tag_id)
);
COMMENT ON TABLE workhour_entry_tag IS '工时明细与标签关联表';

CREATE TABLE IF NOT EXISTS review_log (
    id                  BIGSERIAL PRIMARY KEY,
    biz_type            VARCHAR(32) NOT NULL,
    biz_id              BIGINT NOT NULL,
    review_type         VARCHAR(32) NOT NULL,
    reviewer_id         BIGINT NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    action_code         VARCHAR(32) NOT NULL,
    review_note         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE review_log IS '审核日志表';

CREATE INDEX IF NOT EXISTS idx_review_log_biz ON review_log(biz_type, biz_id, created_at DESC);

CREATE TABLE IF NOT EXISTS todo_item (
    id                  BIGSERIAL PRIMARY KEY,
    todo_type           VARCHAR(32) NOT NULL,
    source_biz_type     VARCHAR(32) NOT NULL,
    source_biz_id       BIGINT NOT NULL,
    title               VARCHAR(255) NOT NULL,
    content             TEXT,
    assignee_user_id    BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    priority_level      SMALLINT NOT NULL DEFAULT 2,
    status              SMALLINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    CONSTRAINT ck_todo_item_priority CHECK (priority_level IN (1,2,3,4)),
    CONSTRAINT ck_todo_item_status CHECK (status IN (0,1,2))
);
COMMENT ON TABLE todo_item IS '管理员待办池';

CREATE INDEX IF NOT EXISTS idx_todo_item_assignee_status ON todo_item(assignee_user_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS biz_operation_log (
    id                  BIGSERIAL PRIMARY KEY,
    biz_type            VARCHAR(32) NOT NULL,
    biz_id              BIGINT,
    operation_type      VARCHAR(32) NOT NULL,
    operator_user_id    BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    request_id          VARCHAR(64),
    payload_before      JSONB,
    payload_after       JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE biz_operation_log IS '通用业务操作日志表';

COMMIT;
