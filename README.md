# License Control Dashboard

A web-based dashboard for managing software license activations. This application allows you to control and monitor software licenses for different systems.

## Features

- System Management
  - Track pending system registrations
  - View system details and status
- License Generation
  - Generate encrypted license keys
  - Set license duration
- License Validation
  - Validate license keys against system IDs
  - Check license expiration
- Dashboard Overview
  - View pending systems count
  - Monitor active and expired licenses

## Tech Stack

- Frontend: Angular 17 with Angular Material
- Backend: Node.js with Express
- Database: MongoDB
- Authentication: JWT (to be implemented)
- Encryption: CryptoJS

## Prerequisites

- Node.js (v14 or higher)
- MongoDB (v4.4 or higher)
- Angular CLI (v17)

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```bash
   # Install Backend dependencies
   cd Backend
   npm install

   # Install Frontend dependencies
   cd ../Frontend
   npm install
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env` in the Backend directory
   - Update the MongoDB connection string and other settings as needed

4. Start the services:
   ```bash
   # Start MongoDB (if not running)
   mongod

   # Start Backend (from Backend directory)
   npm run dev

   # Start Frontend (from Frontend directory)
   npm start
   ```

5. Access the application:
   - Frontend: http://localhost:4200
   - Backend API: http://localhost:3000

## API Endpoints

### Systems
- `POST /api/systems/register` - Register a new system
- `GET /api/systems` - Get all systems
- `GET /api/systems/pending` - Get pending systems
- `GET /api/systems/:id` - Get system by ID

### Licenses
- `POST /api/licenses/generate` - Generate a new license
- `POST /api/licenses/validate` - Validate a license
- `GET /api/licenses` - Get all licenses

## Security Considerations

1. Change the `LICENSE_SECRET` in production
2. Implement proper authentication and authorization
3. Use HTTPS in production
4. Validate all inputs
5. Implement rate limiting for API endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 