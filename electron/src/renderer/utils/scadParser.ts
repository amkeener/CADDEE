/**
 * Parse OpenSCAD customizer-style variables from .scad source code.
 *
 * Supported formats:
 *   varname = value; // [min:max]
 *   varname = value; // [min:step:max]
 *
 * Section headers:
 *   /* [Section Name] *​/
 */

export interface ScadParam {
  name: string
  value: number
  min: number
  max: number
  step: number
  section: string
}

const SECTION_RE = /\/\*\s*\[([^\]]+)\]\s*\*\//g
const PARAM_RE = /^(\w+)\s*=\s*([\d.]+)\s*;\s*\/\/\s*\[([\d.:]+)\]/gm

export function parseScadParams(scadCode: string): ScadParam[] {
  if (!scadCode) return []

  // Build section map: line number -> section name
  const lines = scadCode.split('\n')
  const sectionRanges: { start: number; name: string }[] = []
  for (let i = 0; i < lines.length; i++) {
    const match = /\/\*\s*\[([^\]]+)\]\s*\*\//.exec(lines[i])
    if (match) {
      sectionRanges.push({ start: i, name: match[1].trim() })
    }
  }

  const getSection = (lineNum: number): string => {
    let section = 'General'
    for (const s of sectionRanges) {
      if (lineNum > s.start) section = s.name
    }
    return section
  }

  const params: ScadParam[] = []
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const match = /^(\w+)\s*=\s*([\d.]+)\s*;\s*\/\/\s*\[([\d.:]+)\]/.exec(line)
    if (!match) continue

    const name = match[1]
    const value = parseFloat(match[2])
    const rangeStr = match[3]
    const parts = rangeStr.split(':').map(Number)

    let min: number, max: number, step: number
    if (parts.length === 2) {
      [min, max] = parts
      step = (max - min) / 100
    } else if (parts.length === 3) {
      [min, step, max] = parts
    } else {
      continue
    }

    if (isNaN(min) || isNaN(max) || isNaN(step) || isNaN(value)) continue

    params.push({ name, value, min, max, step, section: getSection(i) })
  }

  return params
}

/**
 * Replace a variable's value in .scad source code.
 */
export function updateScadParam(scadCode: string, name: string, newValue: number): string {
  const re = new RegExp(`^(${name}\\s*=\\s*)[\\d.]+`, 'm')
  return scadCode.replace(re, `$1${newValue}`)
}
