import React, { useRef, useEffect, useCallback, useState } from 'react';
import { useFieldStore } from '../store/fieldStore';
import { fieldToCanvas, canvasToField, snapToGrid } from '../types/field';

interface FieldCanvasProps {
  width: number;
  height: number;
}

export const FieldCanvas: React.FC<FieldCanvasProps> = ({ width, height }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const isDraggingRef = useRef(false);
  const lastMousePosRef = useRef({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  
  const {
    fieldSizeInches,
    points,
    vectors,
    gridOpacity,
    showLabels,
    zoom,
    panX,
    panY,
    selectedPointId,
    selectedVectorId,
    cursorFieldPos,
    isShiftPressed,
    setZoom,
    setPan,
    setCursorPos,
    setShiftPressed,
    selectPoint,
    selectVector
  } = useFieldStore();

  // Grid rendering function
  const drawGrid = useCallback((ctx: CanvasRenderingContext2D) => {
    const baseSpacing = 23.5; // FTC tile size in inches
    
    // Calculate dynamic grid spacing based on zoom level
    let step_in = baseSpacing;
    if (zoom <= 0.5) {
      step_in = baseSpacing * 4; // 94 inches for very zoomed out
    } else if (zoom <= 1.0) {
      step_in = baseSpacing * 2; // 47 inches
    } else if (zoom <= 2.0) {
      step_in = baseSpacing; // 23.5 inches (standard tile)
    } else if (zoom <= 4.0) {
      step_in = baseSpacing / 2; // 11.75 inches
    } else if (zoom <= 8.0) {
      step_in = baseSpacing / 4; // 5.875 inches
    } else if (zoom <= 16.0) {
      step_in = baseSpacing / 8; // 2.9375 inches
    } else {
      step_in = 1.0; // 1 inch for high zoom
    }

    // Set grid style
    ctx.strokeStyle = `rgba(0, 188, 255, ${gridOpacity})`;
    ctx.lineWidth = 1;

    // Calculate grid lines
    const scale = Math.min(width, height) / fieldSizeInches * zoom;
    const centerX = width / 2 + panX;
    const centerY = height / 2 + panY;
    
    const halfField = fieldSizeInches / 2;
    const numLines = Math.ceil(halfField / step_in) + 10; // Extra lines for panning

    // Draw vertical lines
    for (let i = -numLines; i <= numLines; i++) {
      const fieldX = i * step_in;
      const canvasX = centerX + fieldX * scale;
      
      if (canvasX >= -100 && canvasX <= width + 100) {
        ctx.beginPath();
        ctx.moveTo(canvasX, 0);
        ctx.lineTo(canvasX, height);
        ctx.stroke();
      }
    }

    // Draw horizontal lines
    for (let i = -numLines; i <= numLines; i++) {
      const fieldY = i * step_in;
      const canvasY = centerY - fieldY * scale;
      
      if (canvasY >= -100 && canvasY <= height + 100) {
        ctx.beginPath();
        ctx.moveTo(0, canvasY);
        ctx.lineTo(width, canvasY);
        ctx.stroke();
      }
    }

    // Draw center axes (thicker)
    ctx.strokeStyle = `rgba(0, 188, 255, ${Math.min(gridOpacity * 1.5, 1)})`;
    ctx.lineWidth = 2;
    
    // Center vertical line (Y axis)
    ctx.beginPath();
    ctx.moveTo(centerX, 0);
    ctx.lineTo(centerX, height);
    ctx.stroke();
    
    // Center horizontal line (X axis)
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(width, centerY);
    ctx.stroke();
  }, [width, height, fieldSizeInches, zoom, panX, panY, gridOpacity]);

  // Point rendering function
  const drawPoints = useCallback((ctx: CanvasRenderingContext2D) => {
    points.forEach(point => {
      const canvasPos = fieldToCanvas(point.x, point.y, width, height, fieldSizeInches, zoom, panX, panY);
      
      // Skip if outside visible area
      if (canvasPos.x < -50 || canvasPos.x > width + 50 || canvasPos.y < -50 || canvasPos.y > height + 50) {
        return;
      }

      const radius = point.id === selectedPointId ? 12 : 10;
      const lineWidth = point.id === selectedPointId ? 2 : 1;

      // Draw point circle
      ctx.fillStyle = point.color;
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = lineWidth;
      
      ctx.beginPath();
      ctx.arc(canvasPos.x, canvasPos.y, radius, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // Draw label if enabled
      if (showLabels) {
        ctx.fillStyle = point.color;
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'bottom';
        
        // Background for text
        const metrics = ctx.measureText(point.name);
        const textX = canvasPos.x + 15;
        const textY = canvasPos.y - 10;
        
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(textX - 2, textY - 14, metrics.width + 4, 16);
        
        // Text
        const lightColor = lightenColor(point.color, 0.3);
        ctx.fillStyle = lightColor;
        ctx.fillText(point.name, textX, textY);
      }
    });
  }, [points, width, height, fieldSizeInches, zoom, panX, panY, selectedPointId, showLabels]);

  // Vector rendering function
  const drawVectors = useCallback((ctx: CanvasRenderingContext2D) => {
    vectors.forEach(vector => {
      const startPos = fieldToCanvas(vector.x, vector.y, width, height, fieldSizeInches, zoom, panX, panY);
      
      // Calculate vector length in pixels
      const scale = Math.min(width, height) / fieldSizeInches * zoom;
      const arrowLength = vector.magnitude * scale;
      
      // Calculate end position
      const directionRad = (vector.direction * Math.PI) / 180;
      const endPos = {
        x: startPos.x + arrowLength * Math.cos(directionRad),
        y: startPos.y - arrowLength * Math.sin(directionRad)
      };

      // Skip if outside visible area
      if ((startPos.x < -100 && endPos.x < -100) || (startPos.x > width + 100 && endPos.x > width + 100)) {
        return;
      }

      const lineWidth = vector.id === selectedVectorId ? 3 : 2;
      
      // Draw arrow shaft
      ctx.strokeStyle = vector.color;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = 'round';
      
      ctx.beginPath();
      ctx.moveTo(startPos.x, startPos.y);
      ctx.lineTo(endPos.x, endPos.y);
      ctx.stroke();

      // Draw arrowhead
      const arrowHeadLength = 12;
      const arrowHeadAngle = Math.PI / 6; // 30 degrees

      const head1 = {
        x: endPos.x - arrowHeadLength * Math.cos(directionRad - arrowHeadAngle),
        y: endPos.y + arrowHeadLength * Math.sin(directionRad - arrowHeadAngle)
      };

      const head2 = {
        x: endPos.x - arrowHeadLength * Math.cos(directionRad + arrowHeadAngle),
        y: endPos.y + arrowHeadLength * Math.sin(directionRad + arrowHeadAngle)
      };

      ctx.fillStyle = vector.color;
      ctx.beginPath();
      ctx.moveTo(endPos.x, endPos.y);
      ctx.lineTo(head1.x, head1.y);
      ctx.lineTo(head2.x, head2.y);
      ctx.closePath();
      ctx.fill();

      // Draw label if enabled
      if (showLabels) {
        const labelText = `${vector.name}\n${vector.magnitude.toFixed(1)}in @ ${vector.direction.toFixed(0)}°`;
        
        // Position label on opposite side of vector direction
        const oppositeDirection = directionRad + Math.PI;
        const labelDistance = arrowLength < 30 ? 35 : 20;
        const labelPos = {
          x: startPos.x + labelDistance * Math.cos(oppositeDirection),
          y: startPos.y - labelDistance * Math.sin(oppositeDirection)
        };

        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const lines = labelText.split('\n');
        const lineHeight = 12;
        const totalHeight = lines.length * lineHeight;

        // Background
        const maxWidth = Math.max(...lines.map(line => ctx.measureText(line).width));
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(
          labelPos.x - maxWidth / 2 - 3,
          labelPos.y - totalHeight / 2 - 2,
          maxWidth + 6,
          totalHeight + 4
        );

        // Text
        const lightColor = lightenColor(vector.color, 0.3);
        ctx.fillStyle = lightColor;
        lines.forEach((line, index) => {
          const y = labelPos.y - totalHeight / 2 + (index + 0.5) * lineHeight;
          ctx.fillText(line, labelPos.x, y);
        });
      }
    });
  }, [vectors, width, height, fieldSizeInches, zoom, panX, panY, selectedVectorId, showLabels]);

  // Cursor point rendering
  const drawCursorPoint = useCallback((ctx: CanvasRenderingContext2D) => {
    const canvasPos = fieldToCanvas(cursorFieldPos.x, cursorFieldPos.y, width, height, fieldSizeInches, zoom, panX, panY);
    
    ctx.fillStyle = 'rgba(255, 0, 0, 0.6)';
    ctx.strokeStyle = 'rgba(255, 0, 0, 0.8)';
    ctx.lineWidth = 2;
    
    ctx.beginPath();
    ctx.arc(canvasPos.x, canvasPos.y, 8, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
  }, [cursorFieldPos, width, height, fieldSizeInches, zoom, panX, panY]);

  // Main render function
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Set high DPI scaling
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    // Render layers
    drawGrid(ctx);
    drawPoints(ctx);
    drawVectors(ctx);
    drawCursorPoint(ctx);
  }, [width, height, drawGrid, drawPoints, drawVectors, drawCursorPoint]);

  // Animation loop
  useEffect(() => {
    const animate = () => {
      render();
      animationFrameRef.current = requestAnimationFrame(animate);
    };
    
    animate();
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [render]);

  // Mouse event handlers
  const handleMouseDown = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    
    isDraggingRef.current = true;
    lastMousePosRef.current = { x: mouseX, y: mouseY };
    
    // Update cursor position in field coordinates
    const fieldPos = canvasToField(mouseX, mouseY, width, height, fieldSizeInches, zoom, panX, panY);
    const snappedPos = isShiftPressed ? fieldPos : snapToGrid(fieldPos.x, fieldPos.y, 0.5);
    setCursorPos(snappedPos.x, snappedPos.y);
    
    // Check for point/vector selection
    let selectedSomething = false;
    
    // Check points first
    for (const point of points) {
      const pointCanvas = fieldToCanvas(point.x, point.y, width, height, fieldSizeInches, zoom, panX, panY);
      const distance = Math.sqrt((mouseX - pointCanvas.x) ** 2 + (mouseY - pointCanvas.y) ** 2);
      if (distance <= 12) {
        selectPoint(point.id);
        selectedSomething = true;
        break;
      }
    }
    
    // Check vectors if no point selected
    if (!selectedSomething) {
      for (const vector of vectors) {
        const startCanvas = fieldToCanvas(vector.x, vector.y, width, height, fieldSizeInches, zoom, panX, panY);
        const distance = Math.sqrt((mouseX - startCanvas.x) ** 2 + (mouseY - startCanvas.y) ** 2);
        if (distance <= 15) {
          selectVector(vector.id);
          selectedSomething = true;
          break;
        }
      }
    }
    
    // Clear selection if nothing was clicked
    if (!selectedSomething) {
      selectPoint(null);
      selectVector(null);
    }
  }, [width, height, fieldSizeInches, zoom, panX, panY, isShiftPressed, points, vectors, setCursorPos, selectPoint, selectVector]);

  const handleMouseMove = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    
    // Always update cursor position
    const fieldPos = canvasToField(mouseX, mouseY, width, height, fieldSizeInches, zoom, panX, panY);
    const snappedPos = isShiftPressed ? fieldPos : snapToGrid(fieldPos.x, fieldPos.y, 0.5);
    setCursorPos(snappedPos.x, snappedPos.y);
    
    // Handle panning if dragging
    if (isDraggingRef.current) {
      const deltaX = mouseX - lastMousePosRef.current.x;
      const deltaY = mouseY - lastMousePosRef.current.y;
      
      setPan(panX + deltaX, panY + deltaY);
      lastMousePosRef.current = { x: mouseX, y: mouseY };
    }
  }, [width, height, fieldSizeInches, zoom, panX, panY, isShiftPressed, setCursorPos, setPan]);

  const handleMouseUp = useCallback(() => {
    isDraggingRef.current = false;
  }, []);

  const handleWheel = useCallback((event: React.WheelEvent<HTMLCanvasElement>) => {
    event.preventDefault();
    event.stopPropagation();
    
    // Prevent any default browser behavior
    if (event.cancelable) {
      event.preventDefault();
    }
    
    const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(0.1, Math.min(20, zoom * zoomFactor));
    setZoom(newZoom);
  }, [zoom, setZoom]);

  const handleMouseEnter = useCallback(() => {
    setIsHovering(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsHovering(false);
    isDraggingRef.current = false;
  }, []);

  // Keyboard event handlers
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Shift') {
        setShiftPressed(true);
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.key === 'Shift') {
        setShiftPressed(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [setShiftPressed, handleMouseUp]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      className={`border-2 transition-all duration-200 select-none ${
        isHovering 
          ? 'border-blue-400 shadow-lg shadow-blue-400/20' 
          : 'border-gray-600'
      } ${
        isDraggingRef.current ? 'cursor-grabbing' : 'cursor-crosshair'
      }`}
      style={{ 
        width, 
        height,
        borderRadius: '8px',
        touchAction: 'none' // Prevent touch scrolling
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    />
  );
};

// Utility function to lighten colors
const lightenColor = (color: string, factor: number): string => {
  const hex = color.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  
  const newR = Math.min(255, Math.floor(r + (255 - r) * factor));
  const newG = Math.min(255, Math.floor(g + (255 - g) * factor));
  const newB = Math.min(255, Math.floor(b + (255 - b) * factor));
  
  return `rgb(${newR}, ${newG}, ${newB})`;
};