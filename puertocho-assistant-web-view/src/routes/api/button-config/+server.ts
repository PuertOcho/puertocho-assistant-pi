import { json } from '@sveltejs/kit';
import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

const CONFIG_PATH = join(process.cwd(), 'static', 'buttonConfig.json');

export async function GET() {
  try {
    const configData = readFileSync(CONFIG_PATH, 'utf-8');
    const config = JSON.parse(configData);
    
    return json(config, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
  } catch (error) {
    console.error('Error reading button configuration:', error);
    return json({ error: 'Failed to read configuration' }, { status: 500 });
  }
}

export async function POST({ request }) {
  try {
    const newConfig = await request.json();
    
    // Basic validation
    if (!newConfig.matrixConfig || !newConfig.buttonActions) {
      return json({ error: 'Invalid configuration format' }, { status: 400 });
    }
    
    // Write the new configuration
    writeFileSync(CONFIG_PATH, JSON.stringify(newConfig, null, 2));
    
    return json({ success: true, message: 'Configuration updated successfully' });
  } catch (error) {
    console.error('Error updating button configuration:', error);
    return json({ error: 'Failed to update configuration' }, { status: 500 });
  }
}
