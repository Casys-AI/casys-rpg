import { component$, useSignal, useTask$, $, useVisibleTask$, noSerialize } from '@builder.io/qwik';
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

  // Fetch mock data
  useTask$(async () => {
    if (typeof window === 'undefined') return;
    
    try {
      loading.value = true;
      // TODO: Implement API call
      const mockData = {
        nodes: [
          { id: '1', title: 'Node 1', type: 'concept' },
          { id: '2', title: 'Node 2', type: 'concept' }
        ],
        links: [
          { source: '1', target: '2', type: 'related' }
        ]
      };
      
      data.value = mockData;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Error loading graph data';
      console.error('Error loading graph data:', err);
    } finally {
      loading.value = false;
    }
  });

  // Initialize D3 graph
  useVisibleTask$(({ track }) => {
    track(() => data.value);
    track(() => containerRef.value);

    if (!containerRef.value || !data.value) return;

    const width = containerRef.value.clientWidth;
    const height = containerRef.value.clientHeight;

    // Clear previous graph
    d3.select(containerRef.value).selectAll('*').remove();

    const svg = d3.select(containerRef.value)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const simulation = d3.forceSimulation<Node>(data.value.nodes)
      .force('link', d3.forceLink<Node, Link>(data.value.links).id(d => d.id))
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const links = svg.append('g')
      .selectAll('line')
      .data(data.value.links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6);

    const nodes = svg.append('g')
      .selectAll('circle')
      .data(data.value.nodes)
      .enter()
      .append('circle')
      .attr('r', 5)
      .attr('fill', '#69b3a2');

    simulation.on('tick', () => {
      links
        .attr('x1', d => (d.source as Node).x!)
        .attr('y1', d => (d.source as Node).y!)
        .attr('x2', d => (d.target as Node).x!)
        .attr('y2', d => (d.target as Node).y!);

      nodes
        .attr('cx', d => d.x!)
        .attr('cy', d => d.y!);
    });

    d3Elements.value = noSerialize({
      nodes,
      links,
      simulation
    });
  });

  return (
    <div class="h-full">
      {loading.value ? (
        <div class="flex items-center justify-center h-full">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      ) : error.value ? (
        <div class="text-red-500 p-4">{error.value}</div>
      ) : (
        <div
          ref={containerRef}
          class="w-full h-full"
        />
      )}
    </div>
  );
});
