import { component$, useSignal, useTask$, $, useVisibleTask$, noSerialize } from '@builder.io/qwik';
import { api } from '~/services/api';
import * as d3 from 'd3';

interface Node {
  id: string;
  title: string;
  description?: string;
  type: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface Link {
  source: string | Node;
  target: string | Node;
  type: string;
}

interface D3Elements {
  nodes: d3.Selection<any, any, any, any>;
  links: d3.Selection<any, any, any, any>;
  simulation: d3.Simulation<Node, Link>;
}

export const KnowledgeGraph = component$(() => {
  const containerRef = useSignal<Element>();
  const data = useSignal<{ nodes: Node[]; links: Link[] }>({ nodes: [], links: [] });
  const error = useSignal<string | null>(null);
  const loading = useSignal(true);
  const d3Elements = useSignal<D3Elements>();

  // Fetch data
  useTask$(async () => {
    if (typeof window === 'undefined') return;
    
    try {
      loading.value = true;
      const graphData = await api.getKnowledgeGraph();
      const normalizedData = {
        nodes: Array.isArray(graphData.nodes) ? graphData.nodes : [],
        links: Array.isArray(graphData.links) ? graphData.links : []
      };
      data.value = normalizedData;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Error loading graph data';
      console.error('Error loading graph data:', err);
    } finally {
      loading.value = false;
    }
  });

  // Initialize graph after data is loaded and container is ready
  useVisibleTask$(({ track, cleanup }) => {
    track(() => [containerRef.value, data.value]);
    
    if (!containerRef.value || !data.value?.nodes?.length) return;
    
    // Clear existing content
    const container = d3.select(containerRef.value);
    container.selectAll("*").remove();

    // Create SVG
    const width = containerRef.value.clientWidth || 800;
    const height = containerRef.value.clientHeight || 600;
    
    const svg = container
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Create container group for zoom
    const g = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom as any);

    // Create links
    const links = g
      .selectAll('line')
      .data(data.value.links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1)
      .attr('marker-end', 'url(#arrow)');

    // Add arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999');

    // Create nodes
    const nodes = g
      .selectAll('g')
      .data(data.value.nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .attr('class', 'node');

    // Add circles to nodes
    nodes.append('circle')
      .attr('r', 5)
      .attr('fill', '#69b3a2')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);

    // Add labels to nodes
    nodes.append('text')
      .text((d: Node) => `${d.title} (${d.id})`)
      .attr('x', 8)
      .attr('y', 3)
      .attr('class', 'text-sm fill-gray-700');

    // Add tooltips
    nodes.append('title')
      .text((d: Node) => d.description || d.title);

    // Create simulation
    const simulation = d3.forceSimulation<Node>(data.value.nodes)
      .force('link', d3.forceLink<Node, Link>(data.value.links).id((d) => d.id))
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Store D3 elements with noSerialize
    d3Elements.value = noSerialize({
      nodes,
      links,
      simulation
    });

    // Add drag behavior
    nodes.call(
      d3.drag<any, Node>()
        .on('start', (event, d) => {
          if (!event.active && d3Elements.value) {
            d3Elements.value.simulation.alphaTarget(0.3).restart();
          }
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active && d3Elements.value) {
            d3Elements.value.simulation.alphaTarget(0);
          }
          d.fx = null;
          d.fy = null;
        }) as any
    );

    // Update positions on each tick
    simulation.on('tick', () => {
      if (!d3Elements.value) return;

      links
        .attr('x1', (d: any) => (d.source as Node).x || 0)
        .attr('y1', (d: any) => (d.source as Node).y || 0)
        .attr('x2', (d: any) => (d.target as Node).x || 0)
        .attr('y2', (d: any) => (d.target as Node).y || 0);

      nodes
        .attr('transform', (d: any) => `translate(${d.x || 0},${d.y || 0})`);
    });

    // Cleanup
    cleanup(() => {
      if (d3Elements.value?.simulation) {
        d3Elements.value.simulation.stop();
      }
      container.selectAll("*").remove();
    });
  });

  return (
    <div class="h-full">
      <h2 class="text-lg font-semibold mb-4">Knowledge Graph</h2>
      {loading.value ? (
        <div class="flex items-center justify-center p-4">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      ) : error.value ? (
        <div class="text-red-600 p-4">
          {error.value}
        </div>
      ) : (
        <div 
          ref={containerRef} 
          class="w-full h-[calc(100%-2rem)] bg-white rounded-lg shadow-lg"
        />
      )}
    </div>
  );
});
