'use client';

import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { VisualizationResponse, VizNode } from '@/lib/types';
import { useRouter } from 'next/navigation';

interface D3GraphVisualizationProps {
  data: VisualizationResponse;
  loading?: boolean;
  error?: string;
  onNodeClick?: (nodeId: string) => void;
}

interface D3Node extends VizNode {
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
}

interface D3Link {
  source: string | D3Node;
  target: string | D3Node;
  label: string;
}

export default function D3GraphVisualization({
  data,
  loading = false,
  error,
  onNodeClick,
}: D3GraphVisualizationProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!svgRef.current || loading || error || data.nodes.length === 0) return;

    const width = svgRef.current.clientWidth || 800;
    const height = 600;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    // Create color scale by entity type
    const types = Array.from(new Set(data.nodes.map((n) => n.type)));
    const colorScale = d3.scaleOrdinal<string>().domain(types).range(d3.schemeCategory10);

    // Create force simulation
    const simulation = d3
      .forceSimulation<D3Node>(data.nodes as D3Node[])
      .force('link', d3.forceLink<D3Node, D3Link>().links(data.edges as D3Link[]).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(50));

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Add zoom behavior
    const g = svg.append('g');
    const zoom = d3.zoom<SVGSVGElement, unknown>().on('zoom', (event) => {
      g.attr('transform', event.transform);
    });
    svg.call(zoom);

    // Create links
    const link = g
      .append('g')
      .selectAll('line')
      .data(data.edges as D3Link[])
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1.5);

    // Create nodes
    const node = g
      .append('g')
      .selectAll('circle')
      .data(data.nodes as D3Node[])
      .join('circle')
      .attr('r', (d: D3Node) => d.size)
      .attr('fill', (d: D3Node) => colorScale(d.type))
      .attr('opacity', 0.9)
      .attr('stroke', (d: D3Node) => (d.id === data.center_id ? '#000' : '#fff'))
      .attr('stroke-width', (d: D3Node) => (d.id === data.center_id ? 3 : 2))
      .on('mouseover', function (_event, d: D3Node) {
        setHoveredNode(d.id);
        d3.select(this).attr('opacity', 1).attr('stroke-width', 4);
      })
      .on('mouseout', function (_event, d: D3Node) {
        setHoveredNode(null);
        d3.select(this)
          .attr('opacity', 0.9)
          .attr('stroke-width', (d.id === data.center_id ? 3 : 2));
      })
      .on('click', (_event, d: D3Node) => {
        if (onNodeClick) {
          onNodeClick(d.id);
        } else {
          router.push(`/entity/${d.id}`);
        }
      })
      .call(
        d3.drag<any, D3Node>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Add labels
    const labels = g
      .append('g')
      .selectAll('text')
      .data(data.nodes as D3Node[])
      .join('text')
      .attr('font-size', 12)
      .attr('pointer-events', 'none')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .text((d: D3Node) => d.label)
      .attr('fill', '#333');

    // Add tooltip
    const tooltip = d3
      .select('body')
      .append('div')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px 12px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('opacity', 0);

    node
      .on('mousemove', (event, d: D3Node) => {
        tooltip
          .style('opacity', 1)
          .style('left', event.pageX + 10 + 'px')
          .style('top', event.pageY - 10 + 'px')
          .html(`<strong>${d.label}</strong><br/>Type: ${d.type}<br/>Size: ${d.size}`);
      })
      .on('mouseout', () => {
        tooltip.style('opacity', 0);
      });

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: D3Link) => (d.source as D3Node).x || 0)
        .attr('y1', (d: D3Link) => (d.source as D3Node).y || 0)
        .attr('x2', (d: D3Link) => (d.target as D3Node).x || 0)
        .attr('y2', (d: D3Link) => (d.target as D3Node).y || 0);

      node.attr('cx', (d: D3Node) => d.x || 0).attr('cy', (d: D3Node) => d.y || 0);

      labels.attr('x', (d: D3Node) => d.x || 0).attr('y', (d: D3Node) => d.y || 0);
    });

    // Cleanup
    return () => {
      simulation.stop();
      tooltip.remove();
    };
  }, [data, loading, error, onNodeClick, router]);

  if (loading) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 border border-gray-200 rounded-lg">
        <div className="text-center">
          <div className="inline-block animate-spin mb-2">⏳</div>
          <p className="text-gray-600">Loading visualization...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-red-50 border border-red-200 rounded-lg">
        <div className="text-red-700">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="w-full border border-gray-200 rounded-lg bg-white overflow-hidden">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h3 className="text-lg font-semibold">Graph Visualization</h3>
        <p className="text-sm text-gray-600 mt-1">
          {data.node_count} nodes, {data.edge_count} edges. Drag to pan, scroll to zoom, drag nodes to reposition.
        </p>
      </div>
      <svg ref={svgRef} className="w-full" style={{ height: '600px', display: 'block' }} />
      {hoveredNode && (
        <div className="p-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-700">
          Hovering: <span className="font-semibold">{hoveredNode}</span>
        </div>
      )}
    </div>
  );
}
