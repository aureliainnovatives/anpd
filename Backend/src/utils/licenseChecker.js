const License = require('../models/license.model');
const System = require('../models/system.model');

const checkExpiredLicenses = async () => {
  try {
    const currentTime = new Date();
    const expiredLicenses = await License.find({
      status: 'active',
      expiryDate: { $lt: currentTime }
    });

    for (const license of expiredLicenses) {
      license.status = 'expired';
      await license.save();

      // Update associated system status
      const system = await System.findById(license.systemId);
      if (system) {
        system.status = 'expired';
        await system.save();
      }
    }

    console.log(`Checked ${expiredLicenses.length} licenses for expiration`);
  } catch (error) {
    console.error('Error checking expired licenses:', error);
  }
};

// Run the check every minute
setInterval(checkExpiredLicenses, 60000);

// Run initial check when the server starts
checkExpiredLicenses();

module.exports = {
  checkExpiredLicenses
}; 