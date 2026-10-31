"""
Pre-curated knowledge base of verified Natural Language to SQL examples
for Example-Based Retrieval-Augmented Generation (RAG).

These examples represent standard relational database query patterns across
common business and educational domains (sales, e-commerce, HR, university, inventory).
They serve as structural syntactic references for the LLM.
"""

from typing import List, Dict, Any

SQL_EXAMPLES: List[Dict[str, Any]] = [
    # ── Basic Projections & Selection ──────────────────────────────────────────
    {
        "id": "ex_01",
        "question": "Show all columns and records from the products table",
        "sql_query": "SELECT * FROM products;",
        "category": "select_all",
        "dialect": "general"
    },
    {
        "id": "ex_02",
        "question": "List all products with their names, category, and unit price",
        "sql_query": "SELECT product_name, category, unit_price FROM products;",
        "category": "select_columns",
        "dialect": "general"
    },
    {
        "id": "ex_03",
        "question": "Get distinct departments where employees are currently assigned",
        "sql_query": "SELECT DISTINCT department_id FROM employees WHERE department_id IS NOT NULL;",
        "category": "select_distinct",
        "dialect": "general"
    },

    # ── Filtering (WHERE, Comparison, NULLs, IN, BETWEEN) ─────────────────────
    {
        "id": "ex_04",
        "question": "Find products priced higher than 100 dollars",
        "sql_query": "SELECT product_id, product_name, unit_price FROM products WHERE unit_price > 100 ORDER BY unit_price DESC;",
        "category": "where_comparison",
        "dialect": "general"
    },
    {
        "id": "ex_05",
        "question": "Find all active customers located in either New York, California, or Texas",
        "sql_query": "SELECT customer_id, full_name, state, status FROM customers WHERE status = 'active' AND state IN ('NY', 'CA', 'TX');",
        "category": "where_in",
        "dialect": "general"
    },
    {
        "id": "ex_06",
        "question": "List orders placed between January 1, 2024 and March 31, 2024",
        "sql_query": "SELECT order_id, customer_id, order_date, total_amount FROM orders WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31';",
        "category": "where_between",
        "dialect": "general"
    },
    {
        "id": "ex_07",
        "question": "Show all employees who do not have a manager assigned",
        "sql_query": "SELECT employee_id, first_name, last_name, job_title FROM employees WHERE manager_id IS NULL;",
        "category": "where_null",
        "dialect": "general"
    },
    {
        "id": "ex_08",
        "question": "Find customers whose email address ends with @gmail.com",
        "sql_query": "SELECT customer_id, full_name, email FROM customers WHERE email LIKE '%@gmail.com';",
        "category": "where_like",
        "dialect": "general"
    },
    {
        "id": "ex_09",
        "question": "Retrieve books that are either in stock or have a price less than 20",
        "sql_query": "SELECT book_id, title, price, stock_quantity FROM books WHERE stock_quantity > 0 OR price < 20;",
        "category": "where_boolean_logic",
        "dialect": "general"
    },

    # ── Sorting & Pagination (ORDER BY, LIMIT, OFFSET) ────────────────────────
    {
        "id": "ex_10",
        "question": "Find the top 5 highest earning employees",
        "sql_query": "SELECT employee_id, first_name, last_name, salary FROM employees ORDER BY salary DESC LIMIT 5;",
        "category": "order_limit",
        "dialect": "general"
    },
    {
        "id": "ex_11",
        "question": "List students sorted by enrollment year descending and then by last name ascending",
        "sql_query": "SELECT id, first_name, last_name, enrollment_year, gpa FROM students ORDER BY enrollment_year DESC, last_name ASC;",
        "category": "order_multiple",
        "dialect": "general"
    },
    {
        "id": "ex_12",
        "question": "Get the 10 most recent orders with pagination offset for the second page",
        "sql_query": "SELECT order_id, customer_id, order_date, total_amount FROM orders ORDER BY order_date DESC LIMIT 10 OFFSET 10;",
        "category": "limit_offset",
        "dialect": "general"
    },

    # ── Aggregations (COUNT, SUM, AVG, MIN, MAX) ──────────────────────────────
    {
        "id": "ex_13",
        "question": "Count the total number of registered students in the system",
        "sql_query": "SELECT COUNT(*) AS total_students FROM students;",
        "category": "aggregate_count",
        "dialect": "general"
    },
    {
        "id": "ex_14",
        "question": "Calculate the average salary of all employees",
        "sql_query": "SELECT ROUND(AVG(salary), 2) AS average_salary FROM employees;",
        "category": "aggregate_avg",
        "dialect": "general"
    },
    {
        "id": "ex_15",
        "question": "Calculate the total revenue generated from all completed orders",
        "sql_query": "SELECT SUM(total_amount) AS total_revenue FROM orders WHERE status = 'completed';",
        "category": "aggregate_sum",
        "dialect": "general"
    },
    {
        "id": "ex_16",
        "question": "Find the minimum and maximum price across all products",
        "sql_query": "SELECT MIN(unit_price) AS lowest_price, MAX(unit_price) AS highest_price FROM products;",
        "category": "aggregate_min_max",
        "dialect": "general"
    },
    {
        "id": "ex_17",
        "question": "Count how many unique customers placed an order this month",
        "sql_query": "SELECT COUNT(DISTINCT customer_id) AS active_customer_count FROM orders WHERE order_date >= '2024-01-01';",
        "category": "aggregate_count_distinct",
        "dialect": "general"
    },

    # ── Grouping & Summaries (GROUP BY, HAVING) ───────────────────────────────
    {
        "id": "ex_18",
        "question": "Find the number of employees in each department",
        "sql_query": "SELECT department_id, COUNT(*) AS employee_count FROM employees GROUP BY department_id ORDER BY employee_count DESC;",
        "category": "group_by_count",
        "dialect": "general"
    },
    {
        "id": "ex_19",
        "question": "Calculate the average score for each course and sort from highest to lowest",
        "sql_query": "SELECT course_id, ROUND(AVG(score), 2) AS avg_score, COUNT(*) AS student_count FROM exam_scores GROUP BY course_id ORDER BY avg_score DESC;",
        "category": "group_by_avg",
        "dialect": "general"
    },
    {
        "id": "ex_20",
        "question": "Find departments that have more than 10 employees",
        "sql_query": "SELECT department_id, COUNT(*) AS employee_count FROM employees GROUP BY department_id HAVING COUNT(*) > 10;",
        "category": "group_by_having",
        "dialect": "general"
    },
    {
        "id": "ex_21",
        "question": "Find customer categories with average order value greater than 250",
        "sql_query": "SELECT customer_tier, AVG(order_total) AS avg_order_val FROM orders GROUP BY customer_tier HAVING AVG(order_total) > 250;",
        "category": "group_by_having_avg",
        "dialect": "general"
    },
    {
        "id": "ex_22",
        "question": "List total sales amount and number of transactions grouped by year and month",
        "sql_query": "SELECT strftime('%Y-%m', order_date) AS order_month, COUNT(id) AS order_count, SUM(total_amount) AS monthly_revenue FROM orders GROUP BY strftime('%Y-%m', order_date) ORDER BY order_month DESC;",
        "category": "group_by_date",
        "dialect": "sqlite"
    },

    # ── Relational Joins (INNER JOIN, LEFT JOIN, Multi-table JOIN) ────────────
    {
        "id": "ex_23",
        "question": "List employees along with their department names",
        "sql_query": "SELECT e.id, e.first_name, e.last_name, d.name AS department_name FROM employees e INNER JOIN departments d ON e.department_id = d.id;",
        "category": "join_inner",
        "dialect": "general"
    },
    {
        "id": "ex_24",
        "question": "Show all departments and their employees, including departments with no employees",
        "sql_query": "SELECT d.id, d.name AS department_name, e.first_name, e.last_name FROM departments d LEFT JOIN employees e ON d.id = e.department_id;",
        "category": "join_left",
        "dialect": "general"
    },
    {
        "id": "ex_25",
        "question": "Retrieve all customer orders with customer name, order date, and order total",
        "sql_query": "SELECT o.order_id, c.customer_name, o.order_date, o.total_amount FROM orders o JOIN customers c ON o.customer_id = c.id ORDER BY o.order_date DESC;",
        "category": "join_customers_orders",
        "dialect": "general"
    },
    {
        "id": "ex_26",
        "question": "Show students with courses they are enrolled in and the instructor name",
        "sql_query": "SELECT s.first_name, s.last_name, c.title AS course_title, c.instructor FROM students s JOIN enrollments e ON s.id = e.student_id JOIN courses c ON e.course_id = c.id;",
        "category": "join_three_tables",
        "dialect": "general"
    },
    {
        "id": "ex_27",
        "question": "List all order items including product name, quantity, unit price, and calculated subtotal",
        "sql_query": "SELECT oi.order_id, p.product_name, oi.quantity, oi.unit_price, (oi.quantity * oi.unit_price) AS line_total FROM order_items oi JOIN products p ON oi.product_id = p.id;",
        "category": "join_calculated_column",
        "dialect": "general"
    },
    {
        "id": "ex_28",
        "question": "Find courses that currently have no enrolled students",
        "sql_query": "SELECT c.id, c.course_code, c.title FROM courses c LEFT JOIN enrollments e ON c.id = e.course_id WHERE e.id IS NULL;",
        "category": "join_anti_pattern",
        "dialect": "general"
    },

    # ── Subqueries & Common Table Expressions (CTE) ───────────────────────────
    {
        "id": "ex_29",
        "question": "Find employees who earn more than the average company salary",
        "sql_query": "SELECT employee_id, first_name, last_name, salary FROM employees WHERE salary > (SELECT AVG(salary) FROM employees) ORDER BY salary DESC;",
        "category": "subquery_scalar",
        "dialect": "general"
    },
    {
        "id": "ex_30",
        "question": "List customers who have never placed an order",
        "sql_query": "SELECT id, customer_name, email FROM customers WHERE id NOT IN (SELECT DISTINCT customer_id FROM orders WHERE customer_id IS NOT NULL);",
        "category": "subquery_not_in",
        "dialect": "general"
    },
    {
        "id": "ex_31",
        "question": "Find products that have been ordered in quantities greater than 50 in a single order",
        "sql_query": "SELECT id, product_name, unit_price FROM products WHERE id IN (SELECT product_id FROM order_items WHERE quantity > 50);",
        "category": "subquery_in",
        "dialect": "general"
    },
    {
        "id": "ex_32",
        "question": "Using a CTE, find top selling products with total revenue over 5000",
        "sql_query": "WITH product_sales AS (SELECT product_id, SUM(quantity * unit_price) AS total_revenue FROM order_items GROUP BY product_id) SELECT p.id, p.product_name, ps.total_revenue FROM products p JOIN product_sales ps ON p.id = ps.product_id WHERE ps.total_revenue > 5000 ORDER BY ps.total_revenue DESC;",
        "category": "cte",
        "dialect": "general"
    },
    {
        "id": "ex_33",
        "question": "Using a common table expression, identify high GPA students and their department budgets",
        "sql_query": "WITH honor_students AS (SELECT id, first_name, last_name, gpa, department_id FROM students WHERE gpa >= 3.8) SELECT hs.first_name, hs.last_name, hs.gpa, d.name AS department_name, d.budget FROM honor_students hs JOIN departments d ON hs.department_id = d.id;",
        "category": "cte_join",
        "dialect": "general"
    },

    # ── Conditional Expressions (CASE WHEN) ───────────────────────────────────
    {
        "id": "ex_34",
        "question": "Classify students into Honor, Pass, or Probation status based on GPA",
        "sql_query": "SELECT id, first_name, last_name, gpa, CASE WHEN gpa >= 3.5 THEN 'Honor' WHEN gpa >= 2.0 THEN 'Pass' ELSE 'Probation' END AS academic_standing FROM students;",
        "category": "case_when",
        "dialect": "general"
    },
    {
        "id": "ex_35",
        "question": "Categorize product inventory levels into Low Stock, Medium, or Sufficient",
        "sql_query": "SELECT product_name, stock_quantity, CASE WHEN stock_quantity = 0 THEN 'Out of Stock' WHEN stock_quantity < 10 THEN 'Low Stock' ELSE 'Sufficient' END AS inventory_status FROM products;",
        "category": "case_when_inventory",
        "dialect": "general"
    },

    # ── String & Text Functions ───────────────────────────────────────────────
    {
        "id": "ex_36",
        "question": "Concatenate first name and last name into full employee name",
        "sql_query": "SELECT id, (first_name || ' ' || last_name) AS full_name, email FROM employees;",
        "category": "string_concat",
        "dialect": "sqlite"
    },
    {
        "id": "ex_37",
        "question": "Find users where the lowercased username contains admin",
        "sql_query": "SELECT id, username, email FROM users WHERE LOWER(username) LIKE '%admin%';",
        "category": "string_lower_like",
        "dialect": "general"
    },

    # ── Date & Time Operations ────────────────────────────────────────────────
    {
        "id": "ex_38",
        "question": "Retrieve orders placed in the last 30 days",
        "sql_query": "SELECT order_id, customer_id, order_date, total_amount FROM orders WHERE order_date >= date('now', '-30 days') ORDER BY order_date DESC;",
        "category": "date_relative",
        "dialect": "sqlite"
    },
    {
        "id": "ex_39",
        "question": "Find invoices that are overdue and unpaid",
        "sql_query": "SELECT invoice_id, customer_id, due_date, balance FROM invoices WHERE due_date < CURRENT_DATE AND is_paid = FALSE;",
        "category": "date_overdue",
        "dialect": "general"
    },

    # ── Specialized Domain Inquiries ──────────────────────────────────────────
    {
        "id": "ex_40",
        "question": "List students who scored more than 80 marks in any exam",
        "sql_query": "SELECT DISTINCT s.id, s.first_name, s.last_name, m.score, m.grade FROM students s JOIN enrollments e ON s.id = e.student_id JOIN marks m ON e.id = m.enrollment_id WHERE m.score > 80 ORDER BY m.score DESC;",
        "category": "domain_university_marks",
        "dialect": "sqlite"
    },
    {
        "id": "ex_41",
        "question": "Show average exam score and exam count per course",
        "sql_query": "SELECT c.id, c.course_code, c.title, ROUND(AVG(m.score), 2) AS average_score, COUNT(m.id) AS total_exams FROM courses c JOIN enrollments e ON c.id = e.course_id JOIN marks m ON e.id = m.enrollment_id GROUP BY c.id, c.course_code, c.title ORDER BY average_score DESC;",
        "category": "domain_university_avg",
        "dialect": "sqlite"
    },
    {
        "id": "ex_42",
        "question": "Find students enrolled in more than one course",
        "sql_query": "SELECT s.id, s.first_name, s.last_name, COUNT(e.course_id) AS enrolled_courses_count FROM students s JOIN enrollments e ON s.id = e.student_id GROUP BY s.id, s.first_name, s.last_name HAVING COUNT(e.course_id) > 1 ORDER BY enrolled_courses_count DESC;",
        "category": "domain_university_having",
        "dialect": "sqlite"
    },
    {
        "id": "ex_43",
        "question": "Show top 5 customers by total spending",
        "sql_query": "SELECT c.id, c.name, SUM(o.total_amount) AS total_spent FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name ORDER BY total_spent DESC LIMIT 5;",
        "category": "domain_sales_top_customers",
        "dialect": "general"
    },
    {
        "id": "ex_44",
        "question": "Find products with zero sales in the last 90 days",
        "sql_query": "SELECT p.id, p.product_name, p.unit_price FROM products p WHERE p.id NOT IN (SELECT DISTINCT oi.product_id FROM order_items oi JOIN orders o ON oi.order_id = o.id WHERE o.order_date >= date('now', '-90 days'));",
        "category": "domain_sales_stagnant",
        "dialect": "sqlite"
    },
    {
        "id": "ex_45",
        "question": "Calculate total company payroll expenditure by department",
        "sql_query": "SELECT d.name AS department_name, COUNT(e.id) AS headcount, SUM(e.salary) AS total_payroll, ROUND(AVG(e.salary), 2) AS avg_salary FROM departments d JOIN employees e ON d.id = e.department_id GROUP BY d.id, d.name ORDER BY total_payroll DESC;",
        "category": "domain_hr_payroll",
        "dialect": "general"
    }
]

