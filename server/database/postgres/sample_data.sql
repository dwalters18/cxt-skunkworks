-- Insert sample data aligned with PRD
INSERT INTO customers (customer_code, company_name, contact_name, email, phone, address, city, state, zipcode) VALUES
('CUST001', 'Acme Logistics', 'John Smith', 'john@acmelogistics.com', '555-0101', '123 Main St', 'Houston', 'TX', '77002'),
('CUST002', 'Global Freight Solutions', 'Sarah Johnson', 'sarah@globalfreight.com', '555-0102', '456 Oak Ave', 'Dallas', 'TX', '75201'),
('CUST003', 'Premier Shipping Co', 'Mike Davis', 'mike@premiership.com', '555-0103', '789 Pine St', 'Atlanta', 'GA', '30309');

INSERT INTO carriers (name, mc_number, dot_number, contact_info) VALUES
('Swift Transportation', 'MC-123456', 'DOT-987654', '{"phone": "555-0201", "email": "dispatch@swift.com"}'),
('Schneider National', 'MC-234567', 'DOT-876543', '{"phone": "555-0202", "email": "dispatch@schneider.com"}'),
('J.B. Hunt Transport', 'MC-345678', 'DOT-765432', '{"phone": "555-0203", "email": "dispatch@jbhunt.com"}');

INSERT INTO vehicles (carrier_id, vehicle_number, make, model, year, vin, license_plate, vehicle_type, capacity_weight, capacity_volume, fuel_type, status) VALUES
((SELECT id FROM carriers WHERE name = 'Swift Transportation'), 'SWIFT001', 'Freightliner', 'Cascadia', 2022, '1FUJGBDV8NLSP1234', 'TX-12345', 'TRUCK', 80000.00, 3500.00, 'DIESEL', 'AVAILABLE'),
((SELECT id FROM carriers WHERE name = 'Schneider National'), 'SCH001', 'Peterbilt', '579', 2021, '1XPWD40X1ED123456', 'TX-23456', 'TRUCK', 80000.00, 3500.00, 'DIESEL', 'AVAILABLE'),
((SELECT id FROM carriers WHERE name = 'J.B. Hunt Transport'), 'JBH001', 'Kenworth', 'T680', 2023, '1XKWDB0X5NJ123456', 'TX-34567', 'TRUCK', 80000.00, 3500.00, 'DIESEL', 'AVAILABLE');

-- 20 Austin TX-focused drivers with realistic data
INSERT INTO drivers (id, carrier_id, driver_number, first_name, last_name, email, phone, license_number, license_class, license_expiry, date_of_birth, hire_date, status, current_location, current_address, hours_of_service_remaining) VALUES
-- Swift Transportation drivers (Austin-based)
('d1f8b2c4-5e6f-4a7b-8c9d-0e1f2a3b4c5d', (SELECT id FROM carriers WHERE name = 'Swift Transportation'), 'DRV001', 'Robert', 'Wilson', 'robert.wilson@swift.com', '512-555-0301', 'CDL123456789', 'CDL-A', '2025-12-31', '1985-05-15', '2020-01-15', 'AVAILABLE', ST_GeogFromText('POINT(-97.7431 30.2672)'), 'Austin, TX', 10.5),
('a4c1e5f7-8b9c-7d0e-1f2a-3b4c5d6e7f8a', (SELECT id FROM carriers WHERE name = 'Swift Transportation'), 'DRV002', 'Maria', 'Garcia', 'maria.garcia@swift.com', '512-555-0302', 'CDL456789012', 'CDL-A', '2025-10-15', '1987-03-18', '2020-08-22', 'ON_DUTY', ST_GeogFromText('POINT(-97.7581 30.2851)'), 'North Austin, TX', 8.25),
('c6e3a9b1-0d2f-9e4c-5d6e-7f8a9b0c1d2e', (SELECT id FROM carriers WHERE name = 'Swift Transportation'), 'DRV003', 'Carlos', 'Rodriguez', 'carlos.rodriguez@swift.com', '512-555-0303', 'CDL789012345', 'CDL-A', '2026-03-15', '1990-11-12', '2021-02-10', 'AVAILABLE', ST_GeogFromText('POINT(-97.7094 30.2849)'), 'East Austin, TX', 11.0),
('d7f4c0a2-1e3a-0f5b-6c7d-8e9f0a1b2c3d', (SELECT id FROM carriers WHERE name = 'Swift Transportation'), 'DRV004', 'Jennifer', 'Martinez', 'jennifer.martinez@swift.com', '512-555-0304', 'CDL890123456', 'CDL-A', '2025-08-20', '1983-04-25', '2019-07-18', 'DRIVING', ST_GeogFromText('POINT(-97.6890 30.3077)'), 'Cedar Park, TX', 6.75),
('e8a5b1c3-2f4d-1a6e-7f8a-9b0c1d2e3f4a', (SELECT id FROM carriers WHERE name = 'Swift Transportation'), 'DRV005', 'David', 'Thompson', 'david.thompson@swift.com', '512-555-0305', 'CDL901234567', 'CDL-A', '2026-01-10', '1989-08-03', '2021-09-14', 'AVAILABLE', ST_GeogFromText('POINT(-97.8147 30.2672)'), 'West Austin, TX', 9.5),

-- Schneider National drivers (Austin area)
('e2a9c3d5-6f7a-5b8c-9d0e-1f2a3b4c5d6e', (SELECT id FROM carriers WHERE name = 'Schneider National'), 'DRV006', 'Lisa', 'Anderson', 'lisa.anderson@schneider.com', '512-555-0306', 'CDL234567890', 'CDL-A', '2025-11-30', '1982-09-22', '2019-03-10', 'AVAILABLE', ST_GeogFromText('POINT(-97.7431 30.2672)'), 'Austin, TX', 10.25),
('f9c6a2d4-3a5b-2c7e-8f9a-0b1c2d3e4f5a', (SELECT id FROM carriers WHERE name = 'Schneider National'), 'DRV007', 'Michael', 'Johnson', 'michael.johnson@schneider.com', '512-555-0307', 'CDL345678901', 'CDL-A', '2026-02-28', '1984-07-12', '2019-11-05', 'ON_BREAK', ST_GeogFromText('POINT(-97.6890 30.5077)'), 'Round Rock, TX', 7.0),
('a0b7c3d5-4e6f-3a8b-9c0d-1e2f3a4b5c6d', (SELECT id FROM carriers WHERE name = 'Schneider National'), 'DRV008', 'Sarah', 'Williams', 'sarah.williams@schneider.com', '512-555-0308', 'CDL456789013', 'CDL-A', '2025-09-15', '1986-12-30', '2020-04-20', 'AVAILABLE', ST_GeogFromText('POINT(-97.7431 30.1672)'), 'South Austin, TX', 11.25),
('b1c8d4e6-5f7a-4b9c-0d1e-2f3a4b5c6d7e', (SELECT id FROM carriers WHERE name = 'Schneider National'), 'DRV009', 'Anthony', 'Davis', 'anthony.davis@schneider.com', '512-555-0309', 'CDL567890123', 'CDL-A', '2026-05-12', '1988-02-14', '2021-01-08', 'DRIVING', ST_GeogFromText('POINT(-97.8431 30.3172)'), 'Lakeway, TX', 5.5),
('c2d9e5f7-6a8b-5c0d-1e2f-3a4b5c6d7e8f', (SELECT id FROM carriers WHERE name = 'Schneider National'), 'DRV010', 'Amanda', 'Brown', 'amanda.brown@schneider.com', '512-555-0310', 'CDL678901234', 'CDL-A', '2025-12-05', '1985-06-18', '2020-10-15', 'AVAILABLE', ST_GeogFromText('POINT(-97.6231 30.1972)'), 'Kyle, TX', 9.75),

-- J.B. Hunt Transport drivers (Austin region)
('f3b0d4e6-7a8b-6c9d-0e1f-2a3b4c5d6e7f', (SELECT id FROM carriers WHERE name = 'J.B. Hunt Transport'), 'DRV011', 'James', 'Taylor', 'james.taylor@jbhunt.com', '512-555-0311', 'CDL789012346', 'CDL-A', '2026-01-15', '1988-12-08', '2021-06-01', 'AVAILABLE', ST_GeogFromText('POINT(-97.7431 30.2672)'), 'Austin, TX', 10.0),
('d3e0f6a8-7b9c-6d1e-2f3a-4b5c6d7e8f9a', (SELECT id FROM carriers WHERE name = 'J.B. Hunt Transport'), 'DRV012', 'Jessica', 'Miller', 'jessica.miller@jbhunt.com', '512-555-0312', 'CDL890123457', 'CDL-A', '2025-07-22', '1984-10-05', '2020-03-12', 'ON_DUTY', ST_GeogFromText('POINT(-97.8831 30.4672)'), 'Bee Cave, TX', 8.0),
('e4f1a7b9-8c0d-7e2f-3a4b-5c6d7e8f9a0b', (SELECT id FROM carriers WHERE name = 'J.B. Hunt Transport'), 'DRV013', 'Christopher', 'Jones', 'christopher.jones@jbhunt.com', '512-555-0313', 'CDL901234568', 'CDL-A', '2026-04-18', '1987-01-20', '2021-08-25', 'AVAILABLE', ST_GeogFromText('POINT(-97.6231 30.3872)'), 'Pflugerville, TX', 11.5),
('f5d2e8f0-9c1d-8e3f-4a5b-6c7d8e9f0a1b', (SELECT id FROM carriers WHERE name = 'J.B. Hunt Transport'), 'DRV014', 'Rachel', 'Wilson', 'rachel.wilson@jbhunt.com', '512-555-0314', 'CDL012345678', 'CDL-A', '2025-10-30', '1986-05-28', '2020-12-03', 'SLEEPER', ST_GeogFromText('POINT(-97.9431 30.4172)'), 'Dripping Springs, TX', 0.0),
('a6b3c9d1-0e2f-9a4b-5c6d-7e8f9a0b1c2d', (SELECT id FROM carriers WHERE name = 'J.B. Hunt Transport'), 'DRV015', 'Daniel', 'Moore', 'daniel.moore@jbhunt.com', '512-555-0315', 'CDL123456780', 'CDL-A', '2026-06-14', '1985-09-16', '2020-06-22', 'AVAILABLE', ST_GeogFromText('POINT(-97.6631 30.1272)'), 'Buda, TX', 10.75),

-- Additional Austin area drivers (mixed carriers)
('b7c4d0e2-1f3a-0b5c-6d7e-8f9a0b1c2d3e', (SELECT id FROM carriers WHERE name = 'Swift Transportation'), 'DRV016', 'Patricia', 'Jackson', 'patricia.jackson@swift.com', '512-555-0316', 'CDL234567801', 'CDL-A', '2025-11-08', '1983-03-22', '2019-09-17', 'ON_DUTY', ST_GeogFromText('POINT(-97.7731 30.3972)'), 'Cedar Park, TX', 7.25),
('c8d5e1f3-2a4b-1c6d-7e8f-9a0b1c2d3e4f', (SELECT id FROM carriers WHERE name = 'Schneider National'), 'DRV017', 'Kevin', 'White', 'kevin.white@schneider.com', '512-555-0317', 'CDL345678912', 'CDL-A', '2026-03-25', '1989-07-11', '2021-11-30', 'AVAILABLE', ST_GeogFromText('POINT(-97.5431 30.2172)'), 'Manor, TX', 9.0),
('d9e6f2a4-3b5c-2d7e-8f9a-0b1c2d3e4f5a', (SELECT id FROM carriers WHERE name = 'J.B. Hunt Transport'), 'DRV018', 'Nicole', 'Thomas', 'nicole.thomas@jbhunt.com', '512-555-0318', 'CDL456789023', 'CDL-A', '2025-08-17', '1987-11-04', '2020-05-14', 'DRIVING', ST_GeogFromText('POINT(-97.7031 30.4672)'), 'Leander, TX', 6.25),
('e0f7a3b5-4c6d-3e8f-9a0b-1c2d3e4f5a6b', (SELECT id FROM carriers WHERE name = 'Swift Transportation'), 'DRV019', 'Brandon', 'Harris', 'brandon.harris@swift.com', '512-555-0319', 'CDL567890134', 'CDL-A', '2026-01-28', '1986-08-09', '2020-09-08', 'AVAILABLE', ST_GeogFromText('POINT(-97.8231 30.1872)'), 'Sunset Valley, TX', 10.25),
('f1a8b4c6-5d7e-4f9a-0b1c-2d3e4f5a6b7c', (SELECT id FROM carriers WHERE name = 'Schneider National'), 'DRV020', 'Stephanie', 'Clark', 'stephanie.clark@schneider.com', '512-555-0320', 'CDL678901245', 'CDL-A', '2025-12-12', '1984-12-15', '2019-08-19', 'ON_BREAK', ST_GeogFromText('POINT(-97.6831 30.5172)'), 'Georgetown, TX', 8.75);

-- Update vehicle locations with realistic coordinates
UPDATE vehicles SET current_location = ST_GeogFromText('POINT(-97.7431 30.2672)'), current_address = 'Austin, TX' WHERE vehicle_number = 'SWIFT001';
UPDATE vehicles SET current_location = ST_GeogFromText('POINT(-95.3698 29.7604)'), current_address = 'Houston, TX' WHERE vehicle_number = 'SCH001';
UPDATE vehicles SET current_location = ST_GeogFromText('POINT(-96.7970 32.7767)'), current_address = 'Dallas, TX' WHERE vehicle_number = 'JBH001';

-- Insert Austin TX-focused load data (First batch of 150 loads)
INSERT INTO loads (load_number, customer_id, pickup_location, delivery_location, pickup_address, delivery_address, pickup_date, delivery_date, weight, volume, commodity_type, status, assigned_driver_id, assigned_vehicle_id, rate, distance_miles) VALUES
-- Austin to major Texas cities loads
('LOAD001', (SELECT id FROM customers WHERE customer_code = 'CUST001'), 
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-95.3698 29.7604)'),
 '1201 Barton Springs Rd, Austin, TX 78704', '8800 Northwest Fwy, Houston, TX 77092',
 '2024-07-05 08:00:00', '2024-07-05 15:00:00', 25000.00, 1800.00, 'Electronics', 'ASSIGNED', 'd1f8b2c4-5e6f-4a7b-8c9d-0e1f2a3b4c5d', NULL, 2850.00, 165.2),

('LOAD002', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-96.7970 32.7767)'),
 '500 E Cesar Chavez St, Austin, TX 78701', '1900 Pacific Ave, Dallas, TX 75201',
 '2024-07-05 09:00:00', '2024-07-05 16:30:00', 35000.00, 2200.00, 'Automotive Parts', 'IN_TRANSIT', 'a4c1e5f7-8b9c-7d0e-1f2a-3b4c5d6e7f8a', NULL, 1980.00, 195.5),

('LOAD003', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-98.4936 29.4241)'),
 '2100 Guadalupe St, Austin, TX 78705', '300 Alamo Plaza, San Antonio, TX 78205',
 '2024-07-05 10:00:00', '2024-07-05 13:00:00', 18000.00, 1500.00, 'Consumer Goods', 'DELIVERED', 'e2a9c3d5-6f7a-5b8c-9d0e-1f2a3b4c5d6e', NULL, 950.00, 80.1),

('LOAD004', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-106.4850 31.7619)'),
 '1100 S Lamar Blvd, Austin, TX 78704', '123 Mesa St, El Paso, TX 79901',
 '2024-07-05 06:00:00', '2024-07-06 18:00:00', 42000.00, 2800.00, 'Manufacturing Equipment', 'PICKED_UP', 'f3b0d4e6-7a8b-6c9d-0e1f-2a3b4c5d6e7f', NULL, 4200.00, 550.3),

-- Austin area distribution loads
('LOAD005', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6890 30.5077)'),
 '3000 S IH 35, Austin, TX 78704', '100 W Main St, Round Rock, TX 78664',
 '2024-07-05 11:00:00', '2024-07-05 12:30:00', 8500.00, 850.00, 'Food Products', 'CREATED', NULL, NULL, 285.00, 22.4),

('LOAD006', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6231 30.3872)'),
 '1400 E 6th St, Austin, TX 78702', '15803 Windermere Dr, Pflugerville, TX 78660',
 '2024-07-05 12:00:00', '2024-07-05 13:15:00', 5200.00, 620.00, 'Retail Merchandise', 'CREATED', NULL, NULL, 165.00, 15.8),

('LOAD007', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.8147 30.2672)'),
 '701 Brazos St, Austin, TX 78701', '5555 Bee Cave Rd, West Lake Hills, TX 78746',
 '2024-07-05 13:00:00', '2024-07-05 14:00:00', 3100.00, 280.00, 'Office Supplies', 'ASSIGNED', 'c6e3a9b1-0d2f-9e4c-5d6e-7f8a9b0c1d2e', NULL, 125.00, 8.5),

('LOAD008', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6631 30.1272)'),
 '98 Red River St, Austin, TX 78701', '300 Depot St, Buda, TX 78610',
 '2024-07-05 14:00:00', '2024-07-05 15:30:00', 12800.00, 1100.00, 'Construction Materials', 'CREATED', NULL, NULL, 395.00, 18.2),

('LOAD009', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6231 30.1972)'),
 '1717 W 6th St, Austin, TX 78703', '5600 Kyle Pkwy, Kyle, TX 78640',
 '2024-07-05 15:00:00', '2024-07-05 16:15:00', 9400.00, 950.00, 'Pharmaceutical', 'ASSIGNED', 'd7f4c0a2-1e3a-0f5b-6c7d-8e9f0a1b2c3d', NULL, 285.00, 16.7),

('LOAD010', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.7031 30.4672)'),
 '2901 S Capital of Texas Hwy, Austin, TX 78746', '1011 S Bagdad Rd, Leander, TX 78641',
 '2024-07-05 16:00:00', '2024-07-05 17:30:00', 15600.00, 1400.00, 'Home Appliances', 'CREATED', NULL, NULL, 475.00, 25.3),

-- Inbound Austin loads from major cities
('LOAD011', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-95.3698 29.7604)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '7300 Almeda Rd, Houston, TX 77054', '1500 S MoPac Expy, Austin, TX 78746',
 '2024-07-06 06:00:00', '2024-07-06 12:00:00', 28000.00, 2100.00, 'Chemical Products', 'ASSIGNED', 'e8a5b1c3-2f4d-1a6e-7f8a-9b0c1d2e3f4a', NULL, 2650.00, 165.2),

('LOAD012', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-96.7970 32.7767)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '1200 Main St, Dallas, TX 75202', '411 Barton Springs Rd, Austin, TX 78704',
 '2024-07-06 07:00:00', '2024-07-06 14:00:00', 32000.00, 2400.00, 'Technology Hardware', 'IN_TRANSIT', 'f9c6a2d4-3a5b-2c7e-8f9a-0b1c2d3e4f5a', NULL, 1985.00, 195.5),

('LOAD013', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-98.4936 29.4241)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '1604 Broadway, San Antonio, TX 78215', '2200 Barton Springs Rd, Austin, TX 78746',
 '2024-07-06 08:00:00', '2024-07-06 11:00:00', 19500.00, 1650.00, 'Textiles', 'DELIVERED', 'a0b7c3d5-4e6f-3a8b-9c0d-1e2f3a4b5c6d', NULL, 945.00, 80.1),

-- Austin suburbs and surrounding areas
('LOAD014', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.8831 30.4672)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '4477 Bee Cave Rd, Bee Cave, TX 78738', '600 Congress Ave, Austin, TX 78701',
 '2024-07-06 09:00:00', '2024-07-06 10:30:00', 6800.00, 750.00, 'Luxury Goods', 'CREATED', NULL, NULL, 285.00, 18.5),

('LOAD015', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.9431 30.4172)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '26400 Ranch Road 12, Dripping Springs, TX 78620', '1701 Directors Blvd, Austin, TX 78744',
 '2024-07-06 10:00:00', '2024-07-06 12:00:00', 11200.00, 1050.00, 'Agricultural Products', 'ASSIGNED', 'a0b7c3d5-4e6f-3a8b-9c0d-1e2f3a4b5c6d', NULL, 385.00, 28.2),

-- Continue with more loads in various patterns...
('LOAD016', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.5431 30.2172)'),
 '51 Rainey St, Austin, TX 78701', '12264 FM 973, Manor, TX 78653',
 '2024-07-06 11:00:00', '2024-07-06 12:30:00', 7300.00, 680.00, 'Building Materials', 'CREATED', NULL, NULL, 225.00, 12.8),

('LOAD017', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6831 30.5172)'),
 '1100 E 11th St, Austin, TX 78702', '1003 Inner Loop, Georgetown, TX 78628',
 '2024-07-06 12:00:00', '2024-07-06 14:00:00', 13500.00, 1250.00, 'Medical Equipment', 'ASSIGNED', 'b1c8d4e6-5f7a-4b9c-0d1e-2f3a4b5c6d7e', NULL, 485.00, 32.5),

('LOAD018', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.8431 30.3172)'),
 '2400 E Cesar Chavez St, Austin, TX 78702', '1200 Lakeway Dr, Lakeway, TX 78734',
 '2024-07-06 13:00:00', '2024-07-06 14:30:00', 8700.00, 820.00, 'Sporting Goods', 'CREATED', NULL, NULL, 295.00, 15.2),

('LOAD019', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.7731 30.3972)'),
 '301 Congress Ave, Austin, TX 78701', '1890 Ranch Shopping Ctr, Cedar Park, TX 78613',
 '2024-07-06 14:00:00', '2024-07-06 15:45:00', 9800.00, 950.00, 'Electronics Accessories', 'IN_TRANSIT', 'a4c1e5f7-8b9c-7d0e-1f2a-3b4c5d6e7f8a', NULL, 345.00, 19.8),

('LOAD020', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6431 30.4072)'),
 '1250 S Lamar Blvd, Austin, TX 78704', '500 W Whitestone Blvd, Cedar Park, TX 78613',
 '2024-07-06 15:00:00', '2024-07-06 16:30:00', 12100.00, 1150.00, 'Furniture', 'CREATED', NULL, NULL, 395.00, 22.1),

-- Long haul loads from Austin to other major US cities
('LOAD021', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-118.2437 34.0522)'),
 '400 W 2nd St, Austin, TX 78701', '1201 S Figueroa St, Los Angeles, CA 90015',
 '2024-07-07 05:00:00', '2024-07-09 18:00:00', 38000.00, 3200.00, 'Technology Equipment', 'CREATED', NULL, NULL, 8500.00, 1377.8),

('LOAD022', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-87.6298 41.8781)'),
 '1615 S Congress Ave, Austin, TX 78704', '233 S Wacker Dr, Chicago, IL 60606',
 '2024-07-07 06:00:00', '2024-07-09 14:00:00', 31000.00, 2650.00, 'Industrial Machinery', 'ASSIGNED', 'e4f1a7b9-8c0d-7e2f-3a4b-5c6d7e8f9a0b', NULL, 6850.00, 925.4),

('LOAD023', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-104.9903 39.7392)'),
 '98 San Jacinto Blvd, Austin, TX 78701', '1700 Lincoln St, Denver, CO 80203',
 '2024-07-07 07:00:00', '2024-07-08 20:00:00', 26500.00, 2100.00, 'Medical Devices', 'CREATED', NULL, NULL, 4750.00, 586.2),

('LOAD024', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-122.4194 37.7749)'),
 '1701 Directors Blvd, Austin, TX 78744', '1 Market St, San Francisco, CA 94105',
 '2024-07-07 08:00:00', '2024-07-10 12:00:00', 28000.00, 2400.00, 'Software Hardware', 'ASSIGNED', 'f5d2e8f0-9c1d-8e3f-4a5b-6c7d8e9f0a1b', NULL, 9200.00, 1456.3),

-- Austin area manufacturing and distribution
('LOAD025', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.6890 30.5077)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '1000 Industrial Blvd, Round Rock, TX 78681', '505 Barton Springs Rd, Austin, TX 78704',
 '2024-07-07 09:00:00', '2024-07-07 11:00:00', 14500.00, 1350.00, 'Manufacturing Parts', 'CREATED', NULL, NULL, 285.00, 22.4),

('LOAD026', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6890 30.5077)'),
 '2200 E 6th St, Austin, TX 78702', '205 W Main St, Round Rock, TX 78664',
 '2024-07-07 10:00:00', '2024-07-07 12:30:00', 8900.00, 890.00, 'Food Service Equipment', 'ASSIGNED', 'c2d9e5f7-6a8b-5c0d-1e2f-3a4b5c6d7e8f', NULL, 225.00, 22.4),

('LOAD027', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.8831 30.4672)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '3800 Bee Cave Rd, Bee Cave, TX 78738', '1100 S Lamar Blvd, Austin, TX 78704',
 '2024-07-07 11:00:00', '2024-07-07 13:00:00', 6200.00, 580.00, 'Retail Display Equipment', 'CREATED', NULL, NULL, 185.00, 18.5),

-- Austin to regional Texas destinations
('LOAD028', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.1431 31.5804)'),
 '1500 E 6th St, Austin, TX 78702', '100 N University Parks Dr, Waco, TX 76701',
 '2024-07-07 12:00:00', '2024-07-07 16:00:00', 19800.00, 1750.00, 'Educational Equipment', 'ASSIGNED', 'a6b3c9d1-0e2f-9a4b-5c6d-7e8f9a0b1c2d', NULL, 825.00, 102.3),

('LOAD029', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-99.1412 29.3013)'),
 '2901 Montopolis Dr, Austin, TX 78741', '1604 Broadway, San Antonio, TX 78215',
 '2024-07-07 13:00:00', '2024-07-07 16:30:00', 22500.00, 1950.00, 'Restaurant Equipment', 'CREATED', NULL, NULL, 895.00, 80.1),

('LOAD030', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.3427 30.6281)'),
 '1100 E 11th St, Austin, TX 78702', '1000 Wonder World Dr, San Marcos, TX 78666',
 '2024-07-07 14:00:00', '2024-07-07 16:00:00', 11400.00, 1050.00, 'Recreation Equipment', 'ASSIGNED', 'a4c1e5f7-8b9c-7d0e-1f2a-3b4c5d6e7f8a', NULL, 385.00, 30.7),

-- Austin suburbs distribution network
('LOAD031', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6231 30.3872)'),
 '3201 Bee Cave Rd, Austin, TX 78746', '1000 E Pecan St, Pflugerville, TX 78660',
 '2024-07-07 15:00:00', '2024-07-07 16:45:00', 7800.00, 720.00, 'Home Improvement', 'CREATED', NULL, NULL, 245.00, 15.8),

('LOAD032', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.5431 30.2172)'),
 '1717 E 6th St, Austin, TX 78702', '18824 Littig Rd, Manor, TX 78653',
 '2024-07-07 16:00:00', '2024-07-07 17:30:00', 9600.00, 880.00, 'Agricultural Equipment', 'ASSIGNED', 'b7c4d0e2-1f3a-0b5c-6d7e-8f9a0b1c2d3e', NULL, 295.00, 12.8),

('LOAD033', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6831 30.5172)'),
 '2400 E Cesar Chavez St, Austin, TX 78702', '707 Austin Ave, Georgetown, TX 78626',
 '2024-07-07 17:00:00', '2024-07-07 19:00:00', 13200.00, 1200.00, 'Healthcare Equipment', 'CREATED', NULL, NULL, 485.00, 32.5),

-- Evening and overnight loads
('LOAD034', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.7031 30.4672)'),
 '1100 S Lamar Blvd, Austin, TX 78704', '2001 S Bagdad Rd, Leander, TX 78641',
 '2024-07-07 18:00:00', '2024-07-07 20:00:00', 10500.00, 980.00, 'Home Electronics', 'ASSIGNED', 'c8d5e1f3-2a4b-1c6d-7e8f-9a0b1c2d3e4f', NULL, 365.00, 25.3),

('LOAD035', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.8431 30.3172)'),
 '51 Rainey St, Austin, TX 78701', '3404 RR 620 S, Lakeway, TX 78734',
 '2024-07-07 19:00:00', '2024-07-07 21:00:00', 8700.00, 810.00, 'Marine Equipment', 'CREATED', NULL, NULL, 295.00, 15.2),

-- Next day loads starting early morning
('LOAD036', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.9431 30.4172)'),
 '301 Congress Ave, Austin, TX 78701', '14200 Hwy 290 W, Dripping Springs, TX 78620',
 '2024-07-08 05:00:00', '2024-07-08 07:30:00', 16800.00, 1520.00, 'Event Equipment', 'ASSIGNED', 'd1f8b2c4-5e6f-4a7b-8c9d-0e1f2a3b4c5d', NULL, 485.00, 28.2),

-- Inbound loads to Austin from major cities
('LOAD037', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-95.3698 29.7604)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '1200 Travis St, Houston, TX 77002', '98 San Jacinto Blvd, Austin, TX 78701',
 '2024-07-08 06:00:00', '2024-07-08 09:30:00', 24500.00, 2150.00, 'Petrochemical Products', 'CREATED', NULL, NULL, 1250.00, 162.4),

('LOAD038', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-96.7970 32.7767)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '1508 Commerce St, Dallas, TX 75201', '1100 Congress Ave, Austin, TX 78701',
 '2024-07-08 07:00:00', '2024-07-08 10:30:00', 18900.00, 1650.00, 'Financial Equipment', 'ASSIGNED', 'e2a9c3d5-6f7a-5b8c-9d0e-1f2a3b4c5d6e', NULL, 895.00, 195.2),

('LOAD039', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-106.4869 31.7619)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '123 Santa Fe St, El Paso, TX 79901', '1500 E 6th St, Austin, TX 78702',
 '2024-07-08 04:00:00', '2024-07-08 16:00:00', 32000.00, 2800.00, 'Border Trade Goods', 'CREATED', NULL, NULL, 2850.00, 548.7),

('LOAD040', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-94.0422 30.0638)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '2400 Main St, Beaumont, TX 77701', '2200 E 6th St, Austin, TX 78702',
 '2024-07-08 08:00:00', '2024-07-08 11:30:00', 21500.00, 1900.00, 'Refinery Equipment', 'ASSIGNED', 'f3b0d4e6-7a8b-6c9d-0e1f-2a3b4c5d6e7f', NULL, 1150.00, 200.8),

-- Cross-Texas distribution routes
('LOAD041', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-101.8313 33.5779)'),
 '1615 S Congress Ave, Austin, TX 78704', '1400 8th Ave, Lubbock, TX 79401',
 '2024-07-08 09:00:00', '2024-07-08 15:30:00', 19800.00, 1750.00, 'Agricultural Machinery', 'CREATED', NULL, NULL, 1285.00, 347.2),

('LOAD042', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-98.4936 29.4241)'),
 '400 W 2nd St, Austin, TX 78701', '100 N Main Ave, San Antonio, TX 78205',
 '2024-07-08 10:00:00', '2024-07-08 12:30:00', 15600.00, 1400.00, 'Medical Supplies', 'ASSIGNED', 'd3e0f6a8-7b9c-6d1e-2f3a-4b5c6d7e8f9a', NULL, 695.00, 80.1),

('LOAD043', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-100.4370 25.9018)'),
 '51 Rainey St, Austin, TX 78701', '1000 Main St, Laredo, TX 78040',
 '2024-07-08 11:00:00', '2024-07-08 16:00:00', 28500.00, 2450.00, 'International Trade Goods', 'CREATED', NULL, NULL, 1950.00, 231.4),

-- Austin tech corridor and business park loads
('LOAD044', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.7631 30.3172)'),
 '1701 Directors Blvd, Austin, TX 78744', '9900 Stonelake Blvd, Austin, TX 78759',
 '2024-07-08 12:00:00', '2024-07-08 14:00:00', 12400.00, 1150.00, 'Computer Hardware', 'ASSIGNED', 'd9e6f2a4-3b5c-2d7e-8f9a-0b1c2d3e4f5a', NULL, 385.00, 18.5),

('LOAD045', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6731 30.4572)'),
 '1100 S Lamar Blvd, Austin, TX 78704', '11111 Research Blvd, Austin, TX 78759',
 '2024-07-08 13:00:00', '2024-07-08 15:30:00', 9800.00, 920.00, 'Research Equipment', 'CREATED', NULL, NULL, 295.00, 19.8),

('LOAD046', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.8131 30.3072)'),
 '98 San Jacinto Blvd, Austin, TX 78701', '2901 Capital of Texas Hwy, Austin, TX 78746',
 '2024-07-08 14:00:00', '2024-07-08 16:00:00', 14200.00, 1300.00, 'Office Furniture', 'ASSIGNED', 'c6e3a9b1-0d2f-9e4c-5d6e-7f8a9b0c1d2e', NULL, 425.00, 14.2),

-- Austin airport and logistics hub loads
('LOAD047', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.6698 30.1945)'), ST_GeogFromText('POINT(-97.7431 30.2672)'),
 '3600 Presidential Blvd, Austin, TX 78719', '1100 Congress Ave, Austin, TX 78701',
 '2024-07-08 15:00:00', '2024-07-08 16:30:00', 16800.00, 1520.00, 'Air Freight', 'CREATED', NULL, NULL, 385.00, 12.8),

('LOAD048', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6698 30.1945)'),
 '301 Congress Ave, Austin, TX 78701', '3600 Presidential Blvd, Austin, TX 78719',
 '2024-07-08 16:00:00', '2024-07-08 17:30:00', 11500.00, 1050.00, 'Aviation Parts', 'ASSIGNED', 'd7f4c0a2-1e3a-0f5b-6c7d-8e9f0a1b2c3d', NULL, 295.00, 12.8),

-- Austin education and healthcare loads
('LOAD049', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.7331 30.2872)'),
 '2400 E Cesar Chavez St, Austin, TX 78702', '1601 Trinity St, Austin, TX 78701',
 '2024-07-08 17:00:00', '2024-07-08 18:30:00', 8900.00, 820.00, 'Medical Equipment', 'CREATED', NULL, NULL, 185.00, 5.2),

('LOAD050', (SELECT id FROM customers WHERE customer_code = 'CUST002'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.7231 30.2472)'),
 '1500 E 6th St, Austin, TX 78702', '110 Inner Campus Dr, Austin, TX 78712',
 '2024-07-08 18:00:00', '2024-07-08 19:30:00', 7400.00, 680.00, 'Educational Materials', 'ASSIGNED', 'e8a5b1c3-2f4d-1a6e-7f8a-9b0c1d2e3f4a', NULL, 145.00, 3.8),

-- Weekend loads starting Friday evening
('LOAD051', (SELECT id FROM customers WHERE customer_code = 'CUST003'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.8431 30.4172)'),
 '1717 E 6th St, Austin, TX 78702', '401 Congress Ave, Austin, TX 78701',
 '2024-07-08 19:00:00', '2024-07-08 21:00:00', 12800.00, 1180.00, 'Entertainment Equipment', 'CREATED', NULL, NULL, 385.00, 15.2),

('LOAD052', (SELECT id FROM customers WHERE customer_code = 'CUST001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.5631 30.1872)'),
 '3201 Bee Cave Rd, Austin, TX 78746', '14200 E Old Hwy 20, Del Valle, TX 78617',
 '2024-07-08 20:00:00', '2024-07-08 22:00:00', 18500.00, 1650.00, 'Construction Materials', 'ASSIGNED', 'a4c1e5f7-8b9c-7d0e-1f2a-3b4c5d6e7f8a', NULL, 485.00, 25.8);

-- Insert optimized routes with street-level geometry
INSERT INTO routes (load_id, driver_id, vehicle_id, origin_location, destination_location, route_geometry, planned_distance_miles, planned_duration_minutes, estimated_arrival, status, optimization_score, fuel_estimate, toll_estimate) VALUES
-- Austin to Dallas route (LOAD002)
((SELECT id FROM loads WHERE load_number = 'LOAD002'), 'a4c1e5f7-8b9c-7d0e-1f2a-3b4c5d6e7f8a', (SELECT id FROM vehicles WHERE vehicle_number = 'SWIFT001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-96.7970 32.7767)'),
 ST_GeogFromText('LINESTRING(-97.7431 30.2672, -97.7320 30.2851, -97.7210 30.3145, -97.7045 30.3542, -97.6890 30.3895, -97.6734 30.4234, -97.6523 30.4623, -97.6234 30.5234, -97.5934 30.5834, -97.5634 30.6434, -97.5234 30.7034, -97.4834 30.7634, -97.4434 30.8234, -97.4034 30.8834, -97.3634 30.9434, -97.3234 31.0034, -97.2834 31.0634, -97.2434 31.1234, -97.2034 31.1834, -97.1634 31.2434, -97.1234 31.3034, -97.0834 31.3634, -97.0434 31.4234, -97.0034 31.4834, -96.9634 31.5434, -96.9234 31.6034, -96.8834 31.6634, -96.8434 31.7234, -96.8034 31.7834, -96.7970 32.7767)'),
 195.5, 210, '2024-07-05 16:30:00', 'ACTIVE', 8.5, 65.20, 12.50),

-- Austin to Houston route (LOAD003)
((SELECT id FROM loads WHERE load_number = 'LOAD003'), 'e2a9c3d5-6f7a-5b8c-9d0e-1f2a3b4c5d6e', (SELECT id FROM vehicles WHERE vehicle_number = 'SCH001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-95.3698 29.7604)'),
 ST_GeogFromText('LINESTRING(-97.7431 30.2672, -97.7234 30.2456, -97.6934 30.2156, -97.6634 30.1856, -97.6334 30.1556, -97.6034 30.1256, -97.5734 30.0956, -97.5434 30.0656, -97.5134 30.0356, -97.4834 30.0056, -97.4534 29.9756, -97.4234 29.9456, -97.3934 29.9156, -97.3634 29.8856, -97.3334 29.8556, -97.3034 29.8256, -97.2734 29.7956, -97.2434 29.7756, -97.2134 29.7556, -97.1834 29.7356, -97.1534 29.7256, -97.1234 29.7156, -97.0934 29.7056, -97.0634 29.6956, -97.0334 29.6856, -97.0034 29.6756, -96.9734 29.6656, -96.9434 29.6556, -96.9134 29.6456, -96.8834 29.6356, -96.8534 29.6256, -96.8234 29.6156, -96.7934 29.6056, -96.7634 29.5956, -96.7334 29.5856, -96.7034 29.5756, -96.6734 29.5656, -96.6434 29.5556, -96.6134 29.5456, -96.5834 29.5356, -96.5534 29.5256, -96.5234 29.5156, -96.4934 29.5056, -96.4634 29.4956, -96.4334 29.4856, -96.4034 29.4756, -96.3734 29.4656, -96.3434 29.4556, -96.3134 29.4456, -96.2834 29.4356, -96.2534 29.4256, -96.2234 29.4156, -96.1934 29.4056, -96.1634 29.3956, -96.1334 29.3856, -96.1034 29.3756, -96.0734 29.3656, -96.0434 29.3556, -96.0134 29.3456, -95.9834 29.3356, -95.9534 29.3256, -95.9234 29.3156, -95.8934 29.3056, -95.8634 29.2956, -95.8334 29.2856, -95.8034 29.2756, -95.7734 29.2656, -95.7434 29.2556, -95.7134 29.2456, -95.6834 29.2356, -95.6534 29.2256, -95.6234 29.2156, -95.5934 29.2056, -95.5634 29.1956, -95.5334 29.1856, -95.5034 29.1756, -95.4734 29.1656, -95.4434 29.1556, -95.4134 29.1456, -95.3834 29.1356, -95.3534 29.1256, -95.3698 29.7604)'),
 162.3, 180, '2024-07-05 17:30:00', 'PLANNED', 9.2, 52.40, 8.75),

-- Local Austin route (LOAD005)
((SELECT id FROM loads WHERE load_number = 'LOAD005'), 'c6e3a9b1-0d2f-9e4c-5d6e-7f8a9b0c1d2e', (SELECT id FROM vehicles WHERE vehicle_number = 'JBH001'),
 ST_GeogFromText('POINT(-97.7431 30.2672)'), ST_GeogFromText('POINT(-97.6890 30.5077)'),
 ST_GeogFromText('LINESTRING(-97.7431 30.2672, -97.7400 30.2700, -97.7350 30.2750, -97.7300 30.2800, -97.7250 30.2850, -97.7200 30.2900, -97.7150 30.2950, -97.7100 30.3000, -97.7050 30.3050, -97.7000 30.3100, -97.6950 30.3150, -97.6900 30.3200, -97.6880 30.3250, -97.6860 30.3300, -97.6840 30.3350, -97.6820 30.3400, -97.6800 30.3450, -97.6780 30.3500, -97.6760 30.3550, -97.6740 30.3600, -97.6720 30.3650, -97.6700 30.3700, -97.6680 30.3750, -97.6660 30.3800, -97.6640 30.3850, -97.6620 30.3900, -97.6600 30.3950, -97.6580 30.4000, -97.6560 30.4050, -97.6540 30.4100, -97.6520 30.4150, -97.6500 30.4200, -97.6480 30.4250, -97.6460 30.4300, -97.6440 30.4350, -97.6420 30.4400, -97.6400 30.4450, -97.6380 30.4500, -97.6360 30.4550, -97.6340 30.4600, -97.6320 30.4650, -97.6300 30.4700, -97.6280 30.4750, -97.6260 30.4800, -97.6240 30.4850, -97.6220 30.4900, -97.6200 30.4950, -97.6180 30.5000, -97.6160 30.5050, -97.6890 30.5077)'),
 22.4, 35, '2024-07-05 12:30:00', 'PLANNED', 9.8, 7.85, 0.00);
