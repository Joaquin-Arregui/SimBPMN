import BaseModule from './base';
import DisableModelingModule from './features/disable-modeling';

import ToggleModeModule from './features/toggle-mode/modeler';

export default {
  __depends__: [
    BaseModule,
    DisableModelingModule,
    ToggleModeModule
  ]
};