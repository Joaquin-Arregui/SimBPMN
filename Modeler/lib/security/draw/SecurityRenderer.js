'use strict';

import inherits from 'inherits-browser';
import BaseRenderer from 'diagram-js/lib/draw/BaseRenderer';

import {
  is
} from 'bpmn-js/lib/util/ModelUtil';
import {
  append as svgAppend,
  create as svgCreate
} from 'tiny-svg';
import { SoD, BoD, UoC } from '../lock'; // Asegúrate de importar UoC

export default function SecurityRender(eventBus, renderType) { 
  BaseRenderer.call(this, eventBus, 1500);

  this.canRender = function(element) {
    return is(element, 'bpmn:ServiceTask');
  };

  this.drawShape = function(parent, shape) {
    var url;
    
    // Verifica el tipo de seguridad del elemento para decidir la imagen
    var securityType = shape.businessObject.securityType;
  
    if (securityType === 'BoD') {
      url = BoD.dataURL; // Imagen de BoD
    } else if (securityType === 'UoC') {
      url = UoC.dataURL; // Imagen de UoC
    } else {
      url = SoD.dataURL; // Imagen de SoD por defecto
    }
  
    var lockGfx = svgCreate('image', {
      x: 0,
      y: 0,
      width: shape.width,
      height: shape.height,
      href: url
    });
  
    svgAppend(parent, lockGfx);
  
    return lockGfx;
  };  
}

inherits(SecurityRender, BaseRenderer);

SecurityRender.$inject = ['eventBus'];
