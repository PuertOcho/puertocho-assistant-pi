#!/usr/bin/env node

/**
 * Utility script to update button configuration
 * Usage: node updateButtonConfig.js
 * 
 * This script can be used to hot-update the button configuration
 * The changes will be picked up automatically by the web interface
 */

import { writeFileSync, readFileSync } from 'fs';
import { join } from 'path';

const CONFIG_PATH = join(process.cwd(), 'static', 'buttonConfig.json');

// Example function to add a new button
function addButton(id, label, icon, iconType, action, category = 'utility') {
  try {
    // Read current configuration
    const configData = readFileSync(CONFIG_PATH, 'utf-8');
    const config = JSON.parse(configData);
    
    // Check if button with this ID already exists
    const existingIndex = config.buttonActions.findIndex(button => button.id === id);
    
    const newButton = {
      id,
      label,
      icon,
      iconType,
      action,
      category
    };
    
    if (existingIndex >= 0) {
      // Update existing button
      config.buttonActions[existingIndex] = newButton;
      console.log(`Updated button with ID ${id}: ${label}`);
    } else {
      // Add new button
      config.buttonActions.push(newButton);
      console.log(`Added new button with ID ${id}: ${label}`);
    }
    
    // Write back to file
    writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
    console.log('Configuration updated successfully!');
    
  } catch (error) {
    console.error('Error updating configuration:', error);
  }
}

// Example function to remove a button
function removeButton(id) {
  try {
    const configData = readFileSync(CONFIG_PATH, 'utf-8');
    const config = JSON.parse(configData);
    
    const initialLength = config.buttonActions.length;
    config.buttonActions = config.buttonActions.filter(button => button.id !== id);
    
    if (config.buttonActions.length < initialLength) {
      writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
      console.log(`Removed button with ID ${id}`);
    } else {
      console.log(`No button found with ID ${id}`);
    }
    
  } catch (error) {
    console.error('Error removing button:', error);
  }
}

// Example function to update matrix configuration
function updateMatrixConfig(rows, cols) {
  try {
    const configData = readFileSync(CONFIG_PATH, 'utf-8');
    const config = JSON.parse(configData);
    
    config.matrixConfig.rows = rows;
    config.matrixConfig.cols = cols;
    
    writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
    console.log(`Matrix configuration updated to ${rows}x${cols}`);
    
  } catch (error) {
    console.error('Error updating matrix configuration:', error);
  }
}

// Command line interface
const args = process.argv.slice(2);
const command = args[0];

switch (command) {
  case 'add':
    if (args.length < 5) {
      console.log('Usage: node updateButtonConfig.js add <id> <label> <icon> <iconType> [action] [category]');
      console.log('iconType: "emoji" or "image"');
      process.exit(1);
    }
    addButton(
      parseInt(args[1]),
      args[2],
      args[3],
      args[4],
      args[5] || `action_${args[1]}`,
      args[6] || 'utility'
    );
    break;
    
  case 'remove':
    if (args.length < 2) {
      console.log('Usage: node updateButtonConfig.js remove <id>');
      process.exit(1);
    }
    removeButton(parseInt(args[1]));
    break;
    
  case 'matrix':
    if (args.length < 3) {
      console.log('Usage: node updateButtonConfig.js matrix <rows> <cols>');
      process.exit(1);
    }
    updateMatrixConfig(parseInt(args[1]), parseInt(args[2]));
    break;
    
  case 'list':
    try {
      const configData = readFileSync(CONFIG_PATH, 'utf-8');
      const config = JSON.parse(configData);
      console.log('Current configuration:');
      console.log(`Matrix: ${config.matrixConfig.rows}x${config.matrixConfig.cols}`);
      console.log('Buttons:');
      config.buttonActions.forEach(button => {
        console.log(`  ${button.id}: ${button.label} (${button.iconType === 'emoji' ? button.icon : `image: ${button.icon}`}) -> ${button.action}`);
      });
    } catch (error) {
      console.error('Error reading configuration:', error);
    }
    break;
    
  default:
    console.log('Available commands:');
    console.log('  add <id> <label> <icon> <iconType> [action] [category] - Add or update a button');
    console.log('  remove <id> - Remove a button');
    console.log('  matrix <rows> <cols> - Update matrix dimensions');
    console.log('  list - List current configuration');
    console.log('');
    console.log('Examples:');
    console.log('  node updateButtonConfig.js add 17 "Weather" "🌤️" "emoji" "get_weather" "information"');
    console.log('  node updateButtonConfig.js add 18 "Settings" "settings_icon.png" "image" "open_settings" "system"');
    console.log('  node updateButtonConfig.js remove 16');
    console.log('  node updateButtonConfig.js matrix 6 4');
    break;
}
