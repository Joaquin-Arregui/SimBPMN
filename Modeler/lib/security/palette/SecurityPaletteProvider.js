import { SoD, BoD, UoC } from '../lock'; // Asegúrate de importar UoC

export default function SecurityPaletteProvider(palette, create, elementFactory) {
  this._create = create;
  this._elementFactory = elementFactory;

  palette.registerProvider(this);
}

SecurityPaletteProvider.$inject = [
  'palette',
  'create',
  'elementFactory'
];

SecurityPaletteProvider.prototype.getPaletteEntries = function() {

  var elementFactory = this._elementFactory,
      create = this._create;

  function startCreate(event, type) {
    var serviceTaskShape = elementFactory.create(
      'shape', { type: 'bpmn:ServiceTask' }
    );
  
    // Asigna el tipo de seguridad al objeto de la tarea de servicio
    if (type === 'SoD') {
      serviceTaskShape.businessObject.securityType = 'SoD';
    } else if (type === 'BoD') {
      serviceTaskShape.businessObject.securityType = 'BoD';
    } else if (type === 'UoC') {
      serviceTaskShape.businessObject.securityType = 'UoC';
    }
  
    // Inicia la creación del elemento
    create.start(event, serviceTaskShape);
  }

  return {
    'create-service-task-sod': {
      group: 'activity',
      title: 'Create a new SoD Security Task',
      imageUrl: SoD.dataURL,
      action: {
        dragstart: function(event) { startCreate(event, 'SoD'); },
        click: function(event) { startCreate(event, 'SoD'); }
      }
    },
    'create-service-task-bod': {
      group: 'activity',
      title: 'Create a new BoD Security Task',
      imageUrl: BoD.dataURL,
      action: {
        dragstart: function(event) { startCreate(event, 'BoD'); },
        click: function(event) { startCreate(event, 'BoD'); }
      }
    },
    'create-service-task-uoc': { // Nueva entrada para UoC
      group: 'activity',
      title: 'Create a new UoC Security Task',
      imageUrl: UoC.dataURL, // Asegúrate de tener la imagen correspondiente en lock.js
      action: {
        dragstart: function(event) { startCreate(event, 'UoC'); },
        click: function(event) { startCreate(event, 'UoC'); }
      }
    }
  };
};
