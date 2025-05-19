import { html } from 'htm/preact';
import { useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry } from '@bpmn-io/properties-panel';


export default function(element) {
  return [
    {
      id: 'Mth',
      element,
      component: MthFunction, 
      isEdited: isNumberEntryEdited 
    }
  ];
}

function MthFunction(props) {
  const { element, id } = props;

  const modeling = useService('modeling');
  const translate = useService('translate');
  const debounce = useService('debounceInput');

  const getValue = () => {
    if (!element || !element.businessObject) {
      return '';
    }
    const value = element.businessObject.Mth;
    return (typeof value !== 'undefined' && !isNaN(value)) ? value.toString() : '';
  };

  const setValue = value => {
    if (typeof value === 'undefined') {
      return;
    }

    if (!element || !element.businessObject) {
      return;
    }

    if (value.trim() === '') {
      modeling.updateProperties(element, {
        Mth: ''
      });
      return;
    }
    const newValue = parseFloat(value);

    if (isNaN(newValue)) {
      return;
    }
    modeling.updateProperties(element, {
      Mth: newValue
    });
  };

  return html`<${TextFieldEntry}
  id=${id}
  element=${element}
  label=${translate('Mth')}
  getValue=${getValue}
  setValue=${setValue}
  debounce=${debounce}
  tooltip=${translate('Ingrese un valor numérico.')}
/>`;
}

function isNumberEntryEdited(element) {
  if (!element || !element.businessObject) {
    return 0;
  }
  const nuValue = element.businessObject.Nu;
  return (typeof nuValue !== 'undefined' && !isNaN(nuValue)) ? nuValue : 0;
}