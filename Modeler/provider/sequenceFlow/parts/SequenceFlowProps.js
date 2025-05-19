import { html } from 'htm/preact';
import { useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry } from '@bpmn-io/properties-panel';
import { is } from 'bpmn-js/lib/util/ModelUtil';


export default function(element) {
  return [
    {
      id: 'sequenceFlow',
      element,
      component: PercentageofBranchesFunction,
      isEdited: isNumberEntryEdited
    }
  ];
}

// PercentageofBranches
function PercentageofBranchesFunction(props) {
  const { element, id } = props;

  const modeling = useService('modeling');
  const translate = useService('translate');
  const debounce = useService('debounceInput');

  const getValue = () => {
    if (!element || !element.businessObject) {
      return '';
    }
    const value = element.businessObject.percentageOfBranches;

    // Si el valor es `NaN` o no es un número válido, retornar cadena vacía para permitir edición
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
        percentageOfBranches: ''
      });
      return;
    }
    const newPercentage = parseInt(value, 10);

    if (isNaN(newPercentage)) {
      return;
    }
    const sourceElement = element.businessObject.sourceRef;

    if (sourceElement && is(sourceElement, 'bpmn:Gateway')) {
      const outgoingFlows = sourceElement.outgoing || [];
      let totalPercentage = 0;
      let filledBranchesCount = 0;
      let sequenceFlowCount = 0;

      outgoingFlows.forEach(flow => {
        if (is(flow, 'bpmn:SequenceFlow')) {
          sequenceFlowCount++;
          const branchPercentage = parseInt(flow.percentageOfBranches || 0, 10);
          totalPercentage += branchPercentage;

          // Cuenta ramas con un porcentaje válido y diferente de cero
          if (branchPercentage > 0 && !isNaN(branchPercentage)) {
            filledBranchesCount++;
          }
        }
      });

      // Añadir la rama actual al total de porcentajes y ramas completadas
      totalPercentage += newPercentage;
      if (newPercentage > 0) {
        filledBranchesCount++;
      }

      // Verifica si el total excede el 100%
      if (totalPercentage > 100) {
        alert('La suma de todas las ramas del Gateway excede el 100%. Ajusta los valores.');
        return;
      }

      // Verifica si se han rellenado todas las ramas y el total no es 100
      if (filledBranchesCount === sequenceFlowCount && totalPercentage !== 100) {
        alert('Todas las ramas están completadas pero el valor total no es 100%. Ajusta los valores.');
        return;
      }
    }

    modeling.updateProperties(element, {
      percentageOfBranches: newPercentage
    });
  };

  return html`<${TextFieldEntry}
    id=${id}
    element=${element}
    label=${translate('Percentage of Branches')}
    getValue=${getValue}
    setValue=${setValue}
    debounce=${debounce}
    tooltip=${translate('Enter the percentage for this branch.')} 
  />`;
}

function isNumberEntryEdited(element) {

  if (!element || !element.businessObject) {
    return '';
  }

  const nuValue = element.businessObject.numberOfExecutions;

  // Retornar el valor tal como está, permitiendo que sea 'NaN' o vacío
  return nuValue;
}