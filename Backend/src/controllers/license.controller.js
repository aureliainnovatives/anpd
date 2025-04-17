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
    expiryDate.setMinutes(expiryDate.getMinutes() + duration);

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

    // Calculate expected expiry based on decrypted data
    const licenseStartTime = new Date(decryptedData.timestamp);
    const expectedExpiryTime = new Date(licenseStartTime.getTime() + (decryptedData.duration * 60000)); // Convert minutes to milliseconds
    const currentTime = new Date();

    // Check if license has expired based on decrypted data
    if (currentTime > expectedExpiryTime) {
      license.status = 'expired';
      system.status = 'expired';
      await Promise.all([license.save(), system.save()]);
      return res.status(400).json({ message: 'License has expired' });
    }

    // Update expiry date if needed
    if (license.expiryDate.getTime() !== expectedExpiryTime.getTime()) {
      license.expiryDate = expectedExpiryTime;
      await license.save();
    }

    res.json({
      valid: true,
      expiryDate: license.expiryDate,
      status: license.status,
      remainingMinutes: Math.floor((expectedExpiryTime - currentTime) / 60000)
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

exports.renewLicense = async (req, res) => {
  try {
    const { licenseKey } = req.body;

    // Find the license
    const license = await License.findOne({ licenseKey });
    if (!license) {
      return res.status(404).json({ message: 'License not found' });
    }

    // Check if license is terminated
    if (license.status === 'terminated') {
      return res.status(400).json({ message: 'Cannot renew a terminated license' });
    }

    // Decrypt and verify license
    const bytes = CryptoJS.AES.decrypt(licenseKey, SECRET_KEY);
    const decryptedData = JSON.parse(bytes.toString(CryptoJS.enc.Utf8));

    // Calculate new expiry date
    const currentTime = new Date();
    const newExpiryDate = new Date(currentTime.getTime() + (decryptedData.duration * 60000)); // Convert minutes to milliseconds

    // Update license
    license.expiryDate = newExpiryDate;
    license.status = 'active';
    license.startDate = currentTime;
    await license.save();

    // Update system status if needed
    const system = await System.findById(license.systemId);
    if (system) {
      system.status = 'activated';
      await system.save();
    }

    res.json({
      success: true,
      license: {
        ...license.toObject(),
        remainingMinutes: decryptedData.duration
      }
    });
  } catch (error) {
    res.status(400).json({ message: 'Invalid license key or renewal failed' });
  }
};

exports.terminateLicense = async (req, res) => {
  try {
    const { licenseKey } = req.body;

    // Find the license
    const license = await License.findOne({ licenseKey });
    if (!license) {
      return res.status(404).json({ message: 'License not found' });
    }

    // Update license status
    license.status = 'terminated';
    await license.save();

    // Update system status
    const system = await System.findById(license.systemId);
    if (system) {
      system.status = 'expired';
      await system.save();
    }

    res.json({
      success: true,
      message: 'License terminated successfully',
      license
    });
  } catch (error) {
    res.status(400).json({ message: 'Error terminating license', error: error.message });
  }
}; 