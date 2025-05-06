import { TOGGLE_MODE_EVENT } from '../../util/EventHelper';

export default function EditorActions(
    eventBus,
    toggleMode,
    pauseSimulation,
    resetSimulation,
    editorActions,
    injector
) {
  var active = false;

  editorActions.register({
  });

  editorActions.register({
  });

  editorActions.register({
  });

  const log = injector.get('log', false);

  log && editorActions.register({
  });

  eventBus.on(TOGGLE_MODE_EVENT, (event) => {
    active = event.active;
  });
}

EditorActions.$inject = [
  'eventBus',
  'toggleMode',
  'pauseSimulation',
  'resetSimulation',
  'editorActions',
  'injector'
];