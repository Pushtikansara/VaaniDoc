const fs = require('fs');
const path = require('path');

const srcDir = 'e:/VaaniDoc/frontend/src';

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(function(file) {
    file = path.join(dir, file);
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory()) { 
      results = results.concat(walk(file));
    } else { 
      if (file.endsWith('.jsx')) results.push(file);
    }
  });
  return results;
}

const files = walk(srcDir);
files.forEach(f => {
  let c = fs.readFileSync(f, 'utf8');
  let original = c;
  c = c.replace(/var\(--([a-z-]+)\)/g, (match, p1) => {
    const valid = ['navy', 'cream', 'sage', 'brown', 'white', 'text-main', 'text-muted', 'text-light', 'border-color', 'bg-app', 'bg-card'];
    if (valid.includes(p1)) {
        return `var(--color-${p1.replace('border-color', 'border')})`;
    }
    // handle specific legacy things if they somehow remain, like --border-light
    if (p1 === 'border-light') return 'var(--color-border)';
    return match;
  });
  if (c !== original) {
    fs.writeFileSync(f, c);
    console.log("Updated", f);
  }
});
