const express = require('express');
const router = express.Router();
const licenseController = require('../controllers/license.controller');

router.post('/generate', licenseController.generateLicense);
router.post('/validate', licenseController.validateLicense);
router.post('/check-activation', licenseController.checkActivation);
router.post('/renew', licenseController.renewLicense);
router.post('/terminate', licenseController.terminateLicense);
router.get('/', licenseController.getLicenses);

module.exports = router; 