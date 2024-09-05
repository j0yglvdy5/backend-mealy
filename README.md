# Mealy - Backend

## Overview

**Mealy** is a full-stack application designed to streamline food ordering for customers and provide comprehensive management tools for food vendors (admins). This repository contains the backend code developed with Flask, SQLAlchemy, and JWT for user authentication, offering a robust server-side API to support the frontend application.

## Authors
- Joygladys Njeri

**Collaborators**:
1. Raymond Korir
2. Adan Bashir

## Features

- User authentication with login and registration.
- Manage meal options (add, modify, delete).
- Set up and manage daily menus.
- Track and manage food orders.
- Monitor and analyze revenue.
- Initial data setup for testing purposes.

## Technologies Used

- **Flask**: A lightweight web framework for Python.
- **SQLAlchemy**: An ORM for database interactions.
- **Flask-JWT-Extended**: For implementing JWT authentication.
- **Flask-CORS**: Used for handling cross-origin requests between the frontend and backend.
- **SQLite**: A lightweight database for storing application data.
- **Flask-Migrate**: For handling database migrations.

## Getting Started

### Prerequisites

- Python (version >= 3.6)
- Flask
- Flask extensions (Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS)

### Installation

1. **Clone the repository:**

    `git clone https://github.com/j0yglvdy5/backend-mealy`

2. **Navigate to the project directory:**

    `cd mealy/backend`

3. **Install the dependencies:**

    `pipenv install`

### Running the Application

1. **Set up the database:**

    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

2. **Start the server:**

    `python app.py`

3. Open your web browser and go to `http://localhost:5555`.

### API Integration

The backend API is designed to interact with the frontend application. Ensure that the frontend is configured to make requests to the correct API endpoints and that CORS is properly set up to allow cross-origin requests.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries or issues regarding this code, please contact me at joynjeri@gmail.com.
