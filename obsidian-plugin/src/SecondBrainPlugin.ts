import { Plugin, Command } from 'obsidian';
import SettingsTab from './SettingsTab';
import SearchModal from './SearchModal';

interface SecondBrainSettings {
  apiUrl: string;
}

const DEFAULT_SETTINGS: SecondBrainSettings = {
  apiUrl: 'http://localhost:8000',
};

export default class SecondBrainPlugin extends Plugin {
  settings: SecondBrainSettings;

  async onload() {
    await this.loadSettings();
    this.addSettingTab(new SettingsTab(this.app, this));

    this.addCommand({
      id: 'search-second-brain',
      name: 'Search Second Brain',
      callback: () => this.openSearchModal(),
    });

    this.addCommand({
      id: 'entity-detail',
      name: 'Entity Detail',
      callback: () => {
        console.log('Entity detail command');
      },
    });

    this.addCommand({
      id: 'graph-explore',
      name: 'Graph Explorer',
      callback: () => {
        console.log('Graph explorer command');
      },
    });
  }

  onunload() {}

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  openSearchModal() {
    new SearchModal(this.app, this.settings.apiUrl).open();
  }
}
