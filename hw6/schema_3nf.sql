CREATE TABLE IF NOT EXISTS countries (
    country_id INT AUTO_INCREMENT PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    is_banned BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS ip_country_map (
    client_ip VARCHAR(100) PRIMARY KEY,
    country_id INT NOT NULL,
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

CREATE TABLE IF NOT EXISTS requests_3nf (
    request_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    request_time TIMESTAMP NULL,
    client_ip VARCHAR(100) NOT NULL,
    gender VARCHAR(50),
    age INT NULL,
    income VARCHAR(100),
    time_of_day VARCHAR(50),
    requested_file VARCHAR(255),
    FOREIGN KEY (client_ip) REFERENCES ip_country_map(client_ip)
);

CREATE TABLE IF NOT EXISTS error_logs_3nf (
    error_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    request_time TIMESTAMP NULL,
    requested_file VARCHAR(255),
    error_code INT
);
