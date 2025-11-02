import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface D3TreeMapProps {
  data: {
    name: string;
    value: number;
    children?: any[];
  };
  width?: number;
  height?: number;
}

export const D3TreeMap = ({ data, width = 800, height = 600 }: D3TreeMapProps) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Create hierarchy
    const root = d3.hierarchy(data)
      .sum(d => d.value)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    // Create treemap layout
    const treemap = d3.treemap<typeof data>()
      .size([width, height])
      .padding(2)
      .round(true);

    treemap(root as any);

    // Color scale
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // Create cells
    const cell = svg.selectAll('g')
      .data(root.leaves())
      .join('g')
      .attr('transform', (d: any) => `translate(${d.x0},${d.y0})`);

    // Add rectangles
    cell.append('rect')
      .attr('width', (d: any) => d.x1 - d.x0)
      .attr('height', (d: any) => d.y1 - d.y0)
      .attr('fill', (d: any) => color(d.parent?.data.name || d.data.name))
      .attr('opacity', 0.8)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Add text labels
    cell.append('text')
      .attr('x', 4)
      .attr('y', 16)
      .text((d: any) => d.data.name)
      .attr('font-size', '12px')
      .attr('fill', '#fff')
      .attr('font-weight', 'bold');

    // Add value labels
    cell.append('text')
      .attr('x', 4)
      .attr('y', 32)
      .text((d: any) => d.value?.toLocaleString())
      .attr('font-size', '10px')
      .attr('fill', '#fff')
      .attr('opacity', 0.8);

  }, [data, width, height]);

  return <svg ref={svgRef}></svg>;
};

interface D3ForceGraphProps {
  nodes: Array<{ id: string; group: number; value?: number }>;
  links: Array<{ source: string; target: string; value?: number }>;
  width?: number;
  height?: number;
}

export const D3ForceGraph = ({ nodes, links, width = 800, height = 600 }: D3ForceGraphProps) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !nodes.length) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height] as any);

    // Create force simulation
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Color scale
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // Create links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d: any) => Math.sqrt(d.value || 1));

    // Create nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', (d: any) => Math.sqrt((d.value || 10) * 5))
      .attr('fill', (d: any) => color(d.group.toString()))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .call(d3.drag<any, any>()
        .on('start', (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event: any, d: any) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }) as any);

    // Add labels
    const label = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text((d: any) => d.id)
      .attr('font-size', 10)
      .attr('dx', 15)
      .attr('dy', 4);

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      label
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, links, width, height]);

  return <svg ref={svgRef}></svg>;
};

interface D3HeatMapProps {
  data: Array<{ x: string; y: string; value: number }>;
  width?: number;
  height?: number;
}

export const D3HeatMap = ({ data, width = 800, height = 400 }: D3HeatMapProps) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data.length) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    const margin = { top: 30, right: 30, bottom: 60, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Get unique x and y values
    const xValues = Array.from(new Set(data.map(d => d.x)));
    const yValues = Array.from(new Set(data.map(d => d.y)));

    // Create scales
    const x = d3.scaleBand()
      .range([0, innerWidth])
      .domain(xValues)
      .padding(0.05);

    const y = d3.scaleBand()
      .range([innerHeight, 0])
      .domain(yValues)
      .padding(0.05);

    // Color scale
    const colorScale = d3.scaleSequential(d3.interpolateYlOrRd)
      .domain([0, d3.max(data, d => d.value) || 100]);

    // Add X axis
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end');

    // Add Y axis
    g.append('g')
      .call(d3.axisLeft(y));

    // Create tooltip
    const tooltip = d3.select('body')
      .append('div')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background-color', 'white')
      .style('border', '1px solid #ddd')
      .style('padding', '10px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000');

    // Add rectangles
    g.selectAll()
      .data(data)
      .join('rect')
      .attr('x', d => x(d.x) || 0)
      .attr('y', d => y(d.y) || 0)
      .attr('width', x.bandwidth())
      .attr('height', y.bandwidth())
      .style('fill', d => colorScale(d.value))
      .style('stroke', 'white')
      .style('stroke-width', 2)
      .on('mouseover', function(_event, d) {
        tooltip.style('visibility', 'visible')
          .html(`X: ${d.x}<br/>Y: ${d.y}<br/>Value: ${d.value.toFixed(2)}`);
      })
      .on('mousemove', function(event) {
        tooltip
          .style('top', (event.pageY - 10) + 'px')
          .style('left', (event.pageX + 10) + 'px');
      })
      .on('mouseout', function() {
        tooltip.style('visibility', 'hidden');
      });

    return () => {
      tooltip.remove();
    };
  }, [data, width, height]);

  return <svg ref={svgRef}></svg>;
};
