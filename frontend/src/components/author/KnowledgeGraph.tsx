import { component$, useSignal, useTask$, $, useVisibleTask$ } from '@builder.io/qwik';
import { api } from '~/services/api';
import * as d3 from 'd3';

interface Node {
  id: string;
  title: string;
}

interface Link {
  source: string;
  target: string;
}

export const KnowledgeGraph = component$(() => {
  const containerRef = useSignal<Element>();
  const data = useSignal<{ nodes: Node[]; links: Link[] }>({ nodes: [], links: [] });
  const error = useSignal<string | null>(null);
  const loading = useSignal(true);
  const simulation = useSignal<any>(null);

  // Fetch data
  useTask$(async () => {
    if (typeof window === 'undefined') return;
    
    try {
      loading.value = true;
      const graphData = await api.getKnowledgeGraph();
      data.value = graphData;
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
    
    if (!containerRef.value || !data.value.nodes.length) return;
    
    // Clear existing content
    const container = d3.select(containerRef.value);
    container.selectAll("*").remove();

    // Create SVG
    const width = containerRef.value.clientWidth;
    const height = containerRef.value.clientHeight;
    
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

    // Create simulation
    simulation.value = d3.forceSimulation(data.value.nodes)
      .force('link', d3.forceLink(data.value.links).id((d: any) => d.id))
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Create links
    const links = g
      .selectAll('line')
      .data(data.value.links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1);

    // Create nodes
    const nodes = g
      .selectAll('g')
      .data(data.value.nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (event) => {
          if (!event.active) simulation.value.alphaTarget(0.3).restart();
          event.subject.fx = event.subject.x;
          event.subject.fy = event.subject.y;
        })
        .on('drag', (event) => {
          event.subject.fx = event.x;
          event.subject.fy = event.y;
        })
        .on('end', (event) => {
          if (!event.active) simulation.value.alphaTarget(0);
          event.subject.fx = null;
          event.subject.fy = null;
        }) as any);

    // Add circles to nodes
    nodes.append('circle')
      .attr('r', 5)
      .attr('fill', '#69b3a2');

    // Add labels to nodes
    nodes.append('text')
      .text((d: any) => d.title)
      .attr('x', 8)
      .attr('y', 3)
      .attr('font-size', '10px');

    // Update positions on tick
    simulation.value.on('tick', () => {
      links
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      nodes.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Cleanup
    cleanup(() => {
      if (simulation.value) simulation.value.stop();
    });
  });

  return (
    <div class="h-full flex flex-col">
      <h2 class="text-lg font-semibold mb-4">Graphe de navigation</h2>
      {loading.value ? (
        <div class="flex-1 flex items-center justify-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      ) : error.value ? (
        <div class="flex-1 flex items-center justify-center text-red-600 p-4">
          {error.value}
        </div>
      ) : (
        <div ref={containerRef} class="flex-1"></div>
      )}
    </div>
  );
});
