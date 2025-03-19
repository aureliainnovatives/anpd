const License = require('../models/license.model');
const System = require('../models/system.model');
const CryptoJS = require('crypto-js');

const SECRET_KEY = process.env.LICENSE_SECRET || '7d65f4e5ff66d78g99hhfg00vg00h0i98d6f5d4dc6f8g9';

exports.generateLicense = async (req, res) => {
  try {
    const { systemId, duration } = req.body;
    
    const system = await System.findById(systemId);
    if (!system) {
      return res.status(404).json({ message: 'System not found' });
    }

    // Generate license key data
    const licenseData = {
      systemId: system._id,
      uniqueId: system.uniqueId,
      duration,
      timestamp: Date.now()
    };

    const licenseKey = CryptoJS.AES.encrypt(
      JSON.stringify(licenseData),
      SECRET_KEY
    ).toString();

    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + duration);

    // Check for existing license and update it, or create new one
    let license = await License.findOne({ systemId: system._id });
    
    if (license) {
      // Update existing license
      license.licenseKey = licenseKey;
      license.duration = duration;
      license.expiryDate = expiryDate;
      license.status = 'active';
      await license.save();
    } else {
      // Create new license if none exists
      license = new License({
        systemId: system._id,
        licenseKey,
        duration,
        expiryDate
      });
      await license.save();
    }
    
    // Update system status
    system.status = 'activated';
    await system.save();

    res.status(201).json(license);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};

exports.validateLicense = async (req, res) => {
  try {
    const { licenseKey, uniqueId } = req.body;

    // Decrypt and verify license
    const bytes = CryptoJS.AES.decrypt(licenseKey, SECRET_KEY);
    const decryptedData = JSON.parse(bytes.toString(CryptoJS.enc.Utf8));

    const license = await License.findOne({ licenseKey });
    if (!license) {
      return res.status(404).json({ message: 'Invalid license' });
    }

    const system = await System.findById(license.systemId);
    if (!system || system.uniqueId !== uniqueId) {
      return res.status(400).json({ message: 'License does not match system' });
    }

    const isExpired = new Date() > license.expiryDate;
    if (isExpired) {
      license.status = 'expired';
      system.status = 'expired';
      await Promise.all([license.save(), system.save()]);
      return res.status(400).json({ message: 'License has expired' });
    }

    res.json({
      valid: true,
      expiryDate: license.expiryDate,
      status: license.status
    });
  } catch (error) {
    res.status(400).json({ message: 'Invalid license key' });
  }
};

exports.checkActivation = async (req, res) => {
  try {
    const { licenseKey } = req.body;
    
    // Find the license in database
    const license = await License.findOne({ licenseKey });
    
    if (!license) {
      return res.json({ isActivated: false });
    }
    
    // Find if there's an active system using this license
    const system = await System.findOne({ 
      _id: license.systemId,
      status: 'activated'
    });
    
    if (system) {
      return res.json({
        isActivated: true,
        systemId: system.uniqueId
      });
    }
    
    return res.json({ isActivated: false });
    
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.getLicenses = async (req, res) => {
  try {
    const licenses = await License.find()
      .populate('systemId', 'uniqueId status systemInfo')
      .lean();
    res.json(licenses);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
}; 