import { html } from 'htm/preact';
import { useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry, CheckboxEntry } from '@bpmn-io/properties-panel';

export default function(element) {
  return [
    {
      id: 'instance',
      element,
      component: instanceFunction,
      isEdited: isNumberEntryEdited
    },
    {
      id: 'security',
      element,
      component: securityFunction,
      isEdited: isCheckboxEntryEdited
    }
  ];
}

function instanceFunction(props) {
  const { element, id } = props;
  const modeling = useService('modeling');
  const translate = useService('translate');
  const debounce = useService('debounceInput');

  const getValue = () => {
    if (!element || !element.businessObject) {
      return '';
    }
    const value = element.businessObject.instance;
    return typeof value === 'string' ? value : '';
  };

  const setValue = (value) => {
    if (!element || !element.businessObject) {
      return;
    }
    modeling.updateModdleProperties(element, element.businessObject, {
      instance: value.trim() !== '' ? value : undefined
    });
  };

  return html`<${TextFieldEntry}
    id=${id}
    element=${element}
    label=${translate('Number of instances')}
    getValue=${getValue}
    setValue=${setValue}
    debounce=${debounce}
    tooltip=${translate('Enter the number of different instances.')} 
  />`;
}

function securityFunction(props) {
    const { element, id } = props;
  
    const modeling = useService('modeling');
    const translate = useService('translate');
  
    const getValue = () => {
      if (!element || !element.businessObject) {
        return false;
      }
      const value = element.businessObject.security;
      return value === true;
    };
  
    const setValue = (value) => {
      if (!element || !element.businessObject) {
        return;
      }
      modeling.updateModdleProperties(element, element.businessObject, {
        security: value === true ? true : undefined
      });
    };
  
    return html`<${CheckboxEntry}
      id=${id}
      element=${element}
      label=${translate('Security')}
      getValue=${getValue}
      setValue=${setValue}
      tooltip=${translate('Enable or disable security setting.')}
    />`;
  }
  

function isNumberEntryEdited(element) {
  if (!element || !element.businessObject) return '';
  return element.businessObject.numberOfExecutions;
}

function isCheckboxEntryEdited(element) {
    if (!element || !element.businessObject) {
      return false;
    }
    const securityValue = element.businessObject.security;
    return typeof securityValue !== 'undefined';
  }
  
  
