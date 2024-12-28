<script lang="ts">
  export let className = '';
</script>

<footer class="py-8 mt-20 {className}">
  <div class="text-center text-game-secondary font-serif">
    <slot>
      <p>© 2024 CASYS RPG - Une expérience narrative unique</p>
    </slot>
  </div>
</footer>
