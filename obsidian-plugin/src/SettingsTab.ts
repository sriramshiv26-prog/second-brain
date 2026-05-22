import { App, PluginSettingTab, Setting } from 'obsidian';
import SecondBrainPlugin from './SecondBrainPlugin';

export default class SettingsTab extends PluginSettingTab {
  plugin: SecondBrainPlugin;

  constructor(app: App, plugin: SecondBrainPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'Second Brain Settings' });

    new Setting(containerEl)
      .setName('API URL')
      .setDesc('Enter the URL of your Second Brain backend')
      .addText((text) =>
        text
          .setPlaceholder('http://localhost:8000')
          .setValue(this.plugin.settings.apiUrl)
          .onChange(async (value) => {
            this.plugin.settings.apiUrl = value;
            await this.plugin.saveSettings();
          })
      );

    containerEl.createEl('h3', { text: 'Features' });
    containerEl.createEl('p', {
      text: 'Use Cmd+P (Mac) or Ctrl+P (Windows/Linux) and search for "Second Brain" to access available commands.',
    });

    const features = containerEl.createEl('ul');
    features.createEl('li', { text: 'Search Second Brain - Search your knowledge base' });
    features.createEl('li', { text: 'Entity Detail - View entity information and relationships' });
    features.createEl('li', { text: 'Graph Explorer - Explore the knowledge graph' });
  }
}
