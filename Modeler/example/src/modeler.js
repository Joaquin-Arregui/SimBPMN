import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';
import '@bpmn-io/properties-panel/assets/properties-panel.css';
import '../style.less';

import svgPanZoom from 'svg-pan-zoom';
import BpmnModeler from 'bpmn-js/lib/Modeler';
import { debounce } from 'min-dash';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';
import fileOpen from 'file-open';
import download from 'downloadjs';
import exampleXML from '../resources/example.bpmn';
import model1XML from '../resources/model1.bpmn';
import model2XML from '../resources/model2.bpmn';
import model3XML from '../resources/model3.bpmn';
import model4XML from '../resources/model4.bpmn';
import $ from 'jquery';

import securityDrawModule from '../../lib/security/draw';
import securityPaletteModule from '../../lib/security/palette';
import resizeAllModule from '../../lib/resize-all-rules';
import propertiesProviderModule from '../../provider/security';
import securityModdleDescriptor from '../../descriptors/security.json';
import userModdleDescriptor from '../../descriptors/user.json';
import sequenceFlowExtension from '../../descriptors/sequenceFlow.json';
import modelExtension from '../../descriptors/model.json';
import collaborationExtension from '../../descriptors/collaboration.json';
import laneExtension from '../../descriptors/lane.json';
//import participantExtension from '../../descriptors/participant.json';
import participantWithoutLaneExtension from '../../descriptors/participantWithoutLane.json';
import AddExporter from '@bpmn-io/add-exporter';

import {
  esperRules,
  exportToEsper,
  deployRules
} from './taskHandlers';

$(function() {
  const bpmnModeler = new BpmnModeler({
    container: '#canvas',
    propertiesPanel: {
      parent: '#properties-panel'
    },
    additionalModules: [
      BpmnPropertiesPanelModule,
      BpmnPropertiesProviderModule,
      propertiesProviderModule,
      securityPaletteModule,
      securityDrawModule,
      resizeAllModule,
      AddExporter,
    ],
    exporter: {
      name: 'my-bpmn-exporter',
      version: '1.0.0'
    },
    moddleExtensions: {
      security: securityModdleDescriptor,
      user: userModdleDescriptor,
      sequenceFlow: sequenceFlowExtension,
      model: modelExtension,
      collaboration: collaborationExtension,
      lane: laneExtension,
      participantWithoutLane: participantWithoutLaneExtension
    }
  });

  async function openDiagram(xml) {
    try {
      await bpmnModeler.importXML(xml);
      $('#canvas')
        .removeClass('with-error')
        .addClass('with-diagram');
    } catch (err) {
      console.error('Error during importXML:', err);
      $('#canvas')
        .removeClass('with-diagram')
        .addClass('with-error');
      $('#canvas .error pre').text(err.message);
    }
  }

  async function createNewDiagram(modelFile) {
    switch (modelFile) {
      case "example":
        openDiagram(exampleXML);
        break;
      case "model1":
        openDiagram(model1XML);
        break;
      case "model2":
        openDiagram(model2XML);
        break;
      case "model3":
        openDiagram(model3XML);
        break;
      case "model4":
        openDiagram(model4XML);
        break;
      default:
        openDiagram(exampleXML);
    }
  }

  function registerFileDrop(container, callback) {
    function handleFileSelect(e) {
      e.stopPropagation();
      e.preventDefault();

      var files = e.dataTransfer ? e.dataTransfer.files : e.target.files;
      if (files.length === 0) {
        console.error('No se encontró un archivo para procesar.');
        return;
      }

      var file = files[0];

      if (!file || !(file instanceof File)) {
        console.error('El archivo no es válido.');
        return;
      }

      var reader = new FileReader();
      reader.onload = function(e) {
        var xml = e.target.result;
        callback(xml);
      };

      reader.onerror = function(e) {
        console.error('Error al leer el archivo:', e);
      };
      reader.readAsText(file);
    }

    function handleDragOver(e) {
      e.stopPropagation();
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
    }
    container.get(0).addEventListener('dragover', handleDragOver, false);
    container.get(0).addEventListener('drop', handleFileSelect, false);

    var fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.bpmn, .xml';
    fileInput.style.display = 'none';
    fileInput.addEventListener('change', handleFileSelect, false);
    container.get(0).appendChild(fileInput);
  }

  function getQueryParam(param) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
  }
  var modelFile = getQueryParam('model') || 'example';

  createNewDiagram(modelFile);
  registerFileDrop($('#canvas'), openDiagram);

  function setEncoded(link, name, data) {
    if (data) {
      const encodedData = encodeURIComponent(data);
      link.addClass('active').attr({
        'href': 'data:application/json;charset=UTF-8,' + encodedData,
        'download': name
      });
    } else {
      link.removeClass('active');
    }
  }

  var downloadLink = $('#js-download-diagram');
  var downloadSvgLink = $('#js-download-svg');

  let isDownloading = false;
  let hasDownloaded = false;

$('#js-download-esper').off('click').on('click', async function(e) {
  e.preventDefault();
  e.stopPropagation();
  e.stopImmediatePropagation();

  document.querySelector('.modal-overlay').style.display = 'block';
  document.querySelector('#modal-content').textContent = 'Processing simulation...';

  try {
    const content = await exportToEsper(bpmnModeler);

    const response = await fetch('http://localhost:3000/save-esper-file', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content, filename: 'esperTasks.txt' }),
    });
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Server error:', errorText);
      throw new Error(`Error when obtaining violations.txt: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.content.trim()) {
      document.querySelector('#modal-content').textContent = 'No violations found.';
    } else {
      document.querySelector('#modal-content').textContent = data.content;
    }
    document.querySelector('.modal-overlay').style.display = 'block';
      
  } catch (err) {
      console.error('Error al exportar a Esper:', err);
  } finally {
  }
});

$('#js-heat-map').off('click').on('click', async function(e) {
  e.preventDefault();
  e.stopPropagation();
  e.stopImmediatePropagation();

  document.querySelector('.heatModal-overlay').style.display = 'block';
  document.querySelector('#heatModal-content').textContent = 'Processing simulation...';

  try {
      const { xml: diagramXML } = await bpmnModeler.saveXML({format: true});
      const content = await exportToEsper(bpmnModeler);
      const saveResponse = await fetch('http://localhost:3000/heat-map', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content, diagramXML, filename: 'esperTasks.txt', diagramfilename: 'diagram.bpmn' }),
      });
      const data = await saveResponse.json();
      if (data && data.content) {
        await bpmnModeler.importXML(data.content);
        const { svg } = await bpmnModeler.saveSVG();
        await bpmnModeler.importXML(diagramXML);
        document.querySelector('#heatModal-content').innerHTML = svg;
        setTimeout(() => {
          const svgElement = document.querySelector('#heatModal-content svg');
          if (svgElement) {
            svgPanZoom(svgElement, {
              zoomEnabled: true,
              controlIconsEnabled: true,
              fit: true,
              center: true,
            });
          }
        }, 0);
      } else {
        console.error('No diagram XML received.');
      }
  } catch (err) {
      console.error('Error al exportar a Esper:', err);
  } finally {
  }
});

$('#js-heat-map').off('click').on('click', async function(e) {
  e.preventDefault();
  e.stopPropagation();
  e.stopImmediatePropagation();

  document.querySelector('.heatModal-overlay').style.display = 'block';
  document.querySelector('#heatModal-content').textContent = 'Processing simulation...';

  try {
      const { xml: diagramXML } = await bpmnModeler.saveXML({format: true});
      const content = await exportToEsper(bpmnModeler);
      const saveResponse = await fetch('http://localhost:3000/heat-map', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content, diagramXML, filename: 'esperTasks.txt', diagramfilename: 'diagram.bpmn' }),
      });
      const data = await saveResponse.json();
      if (data && data.content) {
        await bpmnModeler.importXML(data.content);
        const { svg } = await bpmnModeler.saveSVG();
        await bpmnModeler.importXML(diagramXML);
        document.querySelector('#heatModal-content').innerHTML = svg;
        setTimeout(() => {
          const svgElement = document.querySelector('#heatModal-content svg');
          if (svgElement) {
            svgPanZoom(svgElement, {
              zoomEnabled: true,
              controlIconsEnabled: true,
              fit: true,
              center: true,
            });
          }
        }, 0);
      } else {
        console.error('No diagram XML received.');
      }
  } catch (err) {
      console.error('Error al exportar a Esper:', err);
  } finally {
      console.log('Proceso de guardado completado');
  }
});

document.getElementById('close-heatModal').addEventListener('click', function() {
  document.querySelector('.heatModal-overlay').style.display = 'none';
});

document.getElementById('close-modal').addEventListener('click', function() {
  document.querySelector('.modal-overlay').style.display = 'none'; 
});

  function downloadDiagram() {
    bpmnModeler.saveXML({ format: true }).then(({ xml }) => {
      download(xml, 'diagram.bpmn', 'application/xml');
    }).catch(err => {
      console.error('Error al guardar BPMN:', err);
    });
  }

  function openFile(files) {
    if (!files.length) return;
    const file = files[0];
    const reader = new FileReader();

    reader.onload = function(event) {
      const xml = event.target.result;
      openDiagram(xml);
    };
    reader.readAsText(file);
  }

  document.body.addEventListener('keydown', function(event) {
    if (event.code === 'KeyS' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      downloadDiagram();
    }

    if (event.code === 'KeyO' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      fileOpen().then(openFile);
    }
  });

  var exportArtifacts = debounce(async function() {
    try {
      const { svg } = await bpmnModeler.saveSVG();
      setEncoded(downloadSvgLink, 'diagram.svg', svg);
    } catch (err) {
      console.error('Error al guardar SVG: ', err);
      setEncoded(downloadSvgLink, 'diagram.svg', null);
    }

    try {
      const { xml } = await bpmnModeler.saveXML({ format: true });
      setEncoded(downloadLink, 'diagram.bpmn', xml);
    } catch (err) {
      console.error('Error al guardar XML: ', err);
      setEncoded(downloadLink, 'diagram.bpmn', null);
    }
  }, 500);

  $('#js-download-json').click(function() {
    try {
      exportArtifacts();
    } catch (err) {
      console.error('Error al exportar artefactos:', err);
    }
  });

  function getQueryParam(param) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
  }
  var modelFile = getQueryParam('model') || 'example';

  createNewDiagram(modelFile);
  registerFileDrop($('#canvas'), openDiagram);

  $('#js-download-diagram').click(function() {
    exportArtifacts();
  });

  bpmnModeler.on('commandStack.changed', () => {
    exportArtifacts();
  });

let isDownloading2 = false;

$('#button2').off('click').on('click', async function(e) {
  e.preventDefault();
  e.stopPropagation();
  e.stopImmediatePropagation();

  if (isDownloading2) return;
  isDownloading2 = true;

  try {
    const content = await deployRules(bpmnModeler);

    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'deployRules.json';

    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Error al exportar Deploy Rules (JSON):', err);
  } finally {
    isDownloading2 = false;
  }
});

  if (!window.FileList || !window.FileReader) {
    window.alert(
      'Parece que usas un navegador antiguo que no soporta arrastrar y soltar. ' +
    'Prueba usar Chrome, Firefox o Internet Explorer > 10.');
  }


$('#js-chatbot').off('click').on('click', async function(e) {
  e.preventDefault();
  e.stopPropagation();
  e.stopImmediatePropagation();

  try {
    const { xml: diagramXML } = await bpmnModeler.saveXML({format: true});
    const content = await exportToEsper(bpmnModeler);

    const response = await fetch('http://localhost:3000/start-chatbot', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ content, diagramXML, filename: 'esperTasks.txt', diagramfilename: 'diagram.bpmn' }),
    });

    if (!response.ok) {
      throw new Error(`Error starting chatbot: ${response.statusText}`);
    }
    const data = await response.json();
    console.log('Server says:', data.message);
    const botResponse = await fetch('http://localhost:3001/newChat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({}),
    });
    if (!botResponse.ok) {
      throw new Error(`Error starting chatbot: ${botResponse.statusText}`);
    }
    const botData = await botResponse.json();
    document.querySelector('.chatbotModal-overlay').style.display = 'block';
    const chatbotContent = document.getElementById('chatbot-content');
    console.log(botData)
    chatbotContent.textContent = "Bot started. " + botData.reply + "\n";
  } catch (err) {
    console.error('Error starting chatbot:', err);
  }
});

document.getElementById('send-chatbot').addEventListener('click', async function() {
  const input = document.getElementById('chatbot-input');
  const message = input.value.trim();
  if (!message) return;

  const chatbotContent = document.getElementById('chatbot-content');
  chatbotContent.textContent += "\nUser: " + message;
  input.value = "";

  try {
    const response = await fetch('http://localhost:3001/continueChat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    if (!response.ok) {
      throw new Error(`Network response was not ok: ${response.statusText}`);
    }
    const data = await response.json();
    chatbotContent.textContent += "\nBot: " + (data.reply || "No reply.");
  } catch (err) {
    console.error('Error sending chat message:', err);
    chatbotContent.textContent += "\nBot: Error processing your message.";
  }
});

document.getElementById('close-chatbotModal').addEventListener('click', function() {
  document.querySelector('.chatbotModal-overlay').style.display = 'none';
});

});