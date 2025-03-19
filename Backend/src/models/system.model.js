const mongoose = require('mongoose');

const systemSchema = new mongoose.Schema({
  uniqueId: {
    type: String,
    required: true,
    unique: true
  },
  status: {
    type: String,
    enum: ['pending', 'activated', 'expired'],
    default: 'pending'
  },
  systemInfo: {
    name: String,
    os: String,
    processor: String
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('System', systemSchema); 