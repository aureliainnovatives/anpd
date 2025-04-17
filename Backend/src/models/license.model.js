const mongoose = require('mongoose');

const licenseSchema = new mongoose.Schema({
  systemId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'System',
    required: true
  },
  licenseKey: {
    type: String,
    required: true,
    unique: true
  },
  duration: {
    type: Number,
    required: true // in days
  },
  startDate: {
    type: Date,
    default: Date.now
  },
  expiryDate: {
    type: Date,
    required: true
  },
  status: {
    type: String,
    enum: ['active', 'expired', 'revoked', 'terminated'],
    default: 'active'
  }
});

module.exports = mongoose.model('License', licenseSchema); 