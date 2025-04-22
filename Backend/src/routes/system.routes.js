const express = require('express');
const router = express.Router();
const systemController = require('../controllers/system.controller');

router.post('/register', systemController.registerSystem);
router.get('/pending', systemController.getPendingSystems);
router.get('/', systemController.getAllSystems);
router.get('/:id', systemController.getSystemById);
router.patch('/:id', systemController.updateSystem);

module.exports = router; 