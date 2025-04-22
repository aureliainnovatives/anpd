const jwt = require('jsonwebtoken');

// Hardcoded credentials (in a real application, these would be stored securely)
const VALID_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

const JWT_SECRET = 'your-secret-key'; // In production, use environment variable

exports.login = (req, res) => {
  const { username, password } = req.body;

  if (username === VALID_CREDENTIALS.username && password === VALID_CREDENTIALS.password) {
    const token = jwt.sign(
      { username: VALID_CREDENTIALS.username },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.json({
      success: true,
      token,
      message: 'Login successful'
    });
  } else {
    res.status(401).json({
      success: false,
      message: 'Invalid credentials'
    });
  }
}; 