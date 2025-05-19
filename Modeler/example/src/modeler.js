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

import resizeAllModule from '../../lib/resize-all-rules';
import propertiesProviderModule from '../../provider/properties';
import userModdleDescriptor from '../../descriptors/user.json';
import sequenceFlowExtension from '../../descriptors/sequenceFlow.json';
import modelExtension from '../../descriptors/model.json';
import collaborationExtension from '../../descriptors/collaboration.json';
import laneExtension from '../../descriptors/lane.json';
import participantWithoutLaneExtension from '../../descriptors/participantWithoutLane.json';
import AddExporter from '@bpmn-io/add-exporter';
import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';

import {
  exportToEsper
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
      resizeAllModule,
      AddExporter,
    ],
    exporter: {
      name: 'my-bpmn-exporter',
      version: '1.0.0'
    },
    moddleExtensions: {
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

  function downloadDiagram() {
    bpmnModeler.saveXML({ format: true }).then(({ xml }) => {
      download(xml, 'diagram.bpmn', 'application/xml');
    }).catch(err => {
      console.error('Error al guardar BPMN:', err);
    });
  }

  document.body.addEventListener('keydown', function(event) {
    if (event.code === 'KeyS' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      downloadDiagram();
    }
  });

  if (!window.FileList || !window.FileReader) {
    window.alert(
      'Parece que usas un navegador antiguo que no soporta arrastrar y soltar. ' +
    'Prueba usar Chrome, Firefox o Internet Explorer > 10.');
  }

  function appendMessage(sender, text) {
    const container = document.getElementById('modal-content-tab3');
    const msgEl = document.createElement('div');
    msgEl.classList.add('message', sender);

    const unsafeHtml = md.render(text);
    const cleanHtml = DOMPurify.sanitize(unsafeHtml);
    msgEl.innerHTML = cleanHtml;

    container.appendChild(msgEl);
    msgEl.scrollIntoView({ block: 'start' });
  }

  const md = new MarkdownIt({
    html:        true,
    linkify:     true,
    typographer: true,
  });

  $('#js-simulate').off('click').on('click', async function(e) {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();

    try {
      const { xml: diagramXML } = await bpmnModeler.saveXML({format: true});
      const content = await exportToEsper(bpmnModeler);

      const response = await fetch('http://localhost:3000/simulate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content, diagramXML, filename: 'esperTasks.txt', diagramfilename: 'diagram.bpmn' }),
      });

      if (!response.ok) {
        throw new Error(`There has been an error in the simulation: ${response.statusText}`);
      }
      const data = await response.json();

      await bpmnModeler.importXML(data.heatMap);
      const { svg } = await bpmnModeler.saveSVG();
      await bpmnModeler.importXML(diagramXML);

      document.querySelector('#modal-content-tab1').textContent = data.simulation;
      document.querySelector('#heatmap-container').innerHTML = svg;
      document.querySelector('#modal-content-tab3').innerHTML = '';
      appendMessage('bot', data.reply);
      document.querySelector('.modal-overlay').style.display = 'block';
    } catch (err) {
      console.error('Error during the simulation:', err);
    }
  });

  $('#js-continue').off('click').on('click', async function(e) {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();

    try {
      document.querySelector('.modal-overlay').style.display = 'block';
    } catch (err) {
      console.error('Error retrieving the simulation:', err);
    }
  });

  document.getElementById('close-modal').addEventListener('click', function() {
    document.querySelector('.modal-overlay').style.display = 'none';
  });

  document.querySelectorAll('.tab-button').forEach(function(button) {
    button.addEventListener('click', function() {
      var tab = this.dataset.tab;
      document.querySelectorAll('.tab-button').forEach(function(btn) {
        btn.classList.remove('active');
      });
      this.classList.add('active');
      document.querySelectorAll('.tab-content').forEach(function(content) {
        content.classList.remove('active');
      });
      document.getElementById(tab + '-content').classList.add('active');
    });
  });

  document.getElementById('send-chatbot').addEventListener('click', async function() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    if (!message) return;

    const llm = document.getElementById('chatbot-selector').value;

    appendMessage('user', message);
    input.value = "";

    try {
      const response = await fetch('http://localhost:3000/continueChat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, llm })
      });
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.statusText}`);
      }
      const data = await response.json();
      appendMessage('bot', (data.reply || "No reply."));
    } catch (err) {
      console.error('Error sending chat message:', err);
      chatbotContent.textContent += "\nBot: Error processing your message.";
    }
  });

  let heatmapPanZoom;
  document.querySelector('[data-tab="tab2"]').addEventListener('click', () => {
    const svgEl = document.querySelector('#heatmap-container svg');
    if (!svgEl) {
      return;
    }
    if (!heatmapPanZoom) {
      heatmapPanZoom = svgPanZoom(svgEl, {
        zoomEnabled: true,
        controlIconsEnabled: true,
        fit: true,
        center: true
      });
    } else {
      heatmapPanZoom.resize();
      heatmapPanZoom.fit();
      heatmapPanZoom.center();
    }
  });

});