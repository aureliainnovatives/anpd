const System = require('../models/system.model');
const License = require('../models/license.model');

exports.registerSystem = async (req, res) => {
  try {
    const { uniqueId, systemInfo } = req.body;
    const system = new System({
      uniqueId,
      systemInfo
    });
    await system.save();
    res.status(201).json(system);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};

exports.getPendingSystems = async (req, res) => {
  try {
    const systems = await System.find({ status: 'pending' });
    res.json(systems);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.getAllSystems = async (req, res) => {
  try {
    const systems = await System.find();
    // Get all licenses
    const licenses = await License.find();
    
    // Map licenses to systems
    const systemsWithLicenses = systems.map(system => {
      const license = licenses.find(l => l.systemId.toString() === system._id.toString());
      return {
        ...system.toObject(),
        license: license || null
      };
    });
    
    res.json(systemsWithLicenses);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.getSystemById = async (req, res) => {
  try {
    const system = await System.findById(req.params.id);
    if (!system) {
      return res.status(404).json({ message: 'System not found' });
    }

    // Get associated license
    const license = await License.findOne({ systemId: system._id });
    
    res.json({
      ...system.toObject(),
      license: license || null
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
}; 