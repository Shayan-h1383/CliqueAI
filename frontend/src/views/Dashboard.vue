<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 px-4 sm:px-6 py-8 sm:py-12">
    <div class="w-full max-w-4xl">
      <div class="text-center mb-8 sm:mb-10">
        <h1 class="dashboard-title text-3xl sm:text-4xl font-extrabold text-gray-800 mb-3">Find your clique</h1>
        <p class="dashboard-subtitle text-base sm:text-lg text-gray-600 min-h-[1.5em] typing-line">
          <span>{{ typedSubtitle }}</span><span class="typing-cursor" v-if="!subtitleTyped"></span>
        </p>
      </div>

      <!-- Goal selection: three explicit cards so order is always left(0) → middle(1) → right(2). Image as background so it fades with the div. -->
      <div class="goal-grid">
        <button
          v-for="(g, idx) in goals"
          :key="g.id"
          type="button"
          class="goal-image-btn group relative rounded-2xl overflow-hidden border-2 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 h-44 sm:h-52 md:h-56"
          :class="[
            goal === g.id ? 'border-primary ring-2 ring-primary/30' : 'border-gray-200 hover:border-primary/50',
            widgetsRevealed ? 'goal-revealed' : 'goal-hidden'
          ]"
          :style="innerStyle(g, idx)"
          @click="goal = g.id"
        >
          <div class="goal-inner absolute inset-0">
            <div
              class="goal-img-bg absolute inset-0 bg-cover bg-center"
              :style="widgetsRevealed ? { backgroundImage: `url(/images/${g.image})` } : {}"
              aria-hidden="true"
            />
            <span class="absolute bottom-0 left-0 right-0 py-2.5 text-center text-white font-bold text-lg sm:text-xl bg-black/50 goal-label">{{ g.label }}</span>
            <div class="absolute top-0 left-0 right-0 bottom-14 flex items-center justify-center p-3 sm:hidden bg-black/50 overlay-desc">
              <p class="text-white text-xs font-medium text-center leading-snug">{{ g.description }}</p>
            </div>
            <div
              class="hidden sm:flex absolute top-0 left-0 right-0 bottom-14 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity items-center justify-center p-4 overlay-desc"
            >
              <p class="text-white text-sm sm:text-base font-medium text-center leading-snug">{{ g.description }}</p>
            </div>
          </div>
        </button>
      </div>

      <form v-if="goal" class="space-y-6" @submit.prevent="submit">
        <!-- Area dropdown -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ areaLabel }}</label>
          <select
            v-model="area"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value="">Select...</option>
            <option v-for="opt in areaOptions" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>

        <!-- Details -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Details</label>
          <textarea
            v-model="details"
            :placeholder="detailsPlaceholder"
            required
            maxlength="500"
            rows="4"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary resize-none"
          />
          <p class="text-sm text-gray-500 mt-1">{{ details.length }}/500</p>
        </div>

        <!-- Third field -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ thirdFieldLabel }}</label>
          <input
            v-model="thirdField"
            type="text"
            :placeholder="thirdFieldPlaceholder"
            required
            maxlength="100"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          />
          <p class="text-sm text-gray-500 mt-1">{{ thirdField.length }}/100</p>
          <p v-if="descriptionWordCount < minDescriptionWords" class="text-sm text-amber-600 mt-1">
            Add a bit more detail ({{ descriptionWordCount }}/{{ minDescriptionWords }} words in details + summary) so we can find better matches.
          </p>
        </div>

        <!-- City -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">City</label>
          <select
            v-model="city"
            required
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          >
            <option value="">Select city...</option>
            <option v-for="c in ukCities" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>

        <div v-if="errorMessage" class="text-red-600 text-sm">{{ errorMessage }}</div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 rounded-lg font-semibold text-white bg-primary hover:bg-primary/90 disabled:opacity-50"
        >
          {{ loading ? 'Submitting...' : 'Submit application' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()

const GOAL_DELAYS_MS = [0, 200, 400]

function innerStyle(g, idx) {
  if (!widgetsRevealed.value) return {}
  return {
    animation: 'goalFadeIn 0.5s ease-out forwards',
    animationDelay: `${GOAL_DELAYS_MS[idx]}ms`,
  }
}

const goals = [
  {
    id: 'evolve',
    label: 'Evolve',
    image: 'butteryfly.jpg.jpeg',
    description: 'Grow and transform — studies, business, arts, sports.',
  },
  {
    id: 'enjoy',
    label: 'Enjoy',
    image: 'women.jpg.jpeg',
    description: 'Have fun and connect — gaming, content, humour, hiking, camping.',
  },
  {
    id: 'support',
    label: 'Support',
    image: 'hands.jpg.jpeg',
    description: 'Give and get support — addiction, relationship, grief, illness.',
  },
]

const imageLoaded = ref([false, false, false])
const allImagesLoaded = computed(() => imageLoaded.value.every(Boolean))
const widgetsRevealed = ref(false)

function markImageLoaded(index) {
  if (imageLoaded.value[index]) return
  const next = imageLoaded.value.slice()
  next[index] = true
  imageLoaded.value = next
}

onMounted(() => {
  goals.forEach((g, i) => {
    const img = new Image()
    img.onload = () => markImageLoaded(i)
    img.src = `/images/${g.image}`
  })
})

watch(allImagesLoaded, (loaded) => {
  if (!loaded) return
  widgetsRevealed.value = true
})

const subtitleText = 'I want to find my clique to:'
const typedSubtitle = ref('')
const subtitleTyped = ref(false)

onMounted(() => {
  const chunk = 2
  let i = 0
  const interval = setInterval(() => {
    i = Math.min(i + chunk, subtitleText.length + 1)
    typedSubtitle.value = subtitleText.slice(0, i)
    if (i > subtitleText.length) {
      subtitleTyped.value = true
      clearInterval(interval)
    }
  }, 80)
})

const minDescriptionWords = 15

const goal = ref('')
const area = ref('')
const details = ref('')
const thirdField = ref('')
const city = ref('')
const loading = ref(false)
const errorMessage = ref('')

const descriptionWordCount = computed(() => {
  const combined = `${(details.value || '').trim()} ${(thirdField.value || '').trim()}`
  return combined ? combined.split(/\s+/).filter(Boolean).length : 0
})

const ukCities = [
  'London', 'Birmingham', 'Manchester', 'Leeds', 'Glasgow', 'Liverpool', 'Bristol', 'Sheffield',
  'Edinburgh', 'Cardiff', 'Belfast', 'Newcastle upon Tyne', 'Nottingham', 'Southampton', 'Brighton',
  'Leicester', 'Coventry', 'Hull', 'Bradford', 'Stoke-on-Trent', 'Wolverhampton', 'Derby',
  'Plymouth', 'Reading', 'Northampton', 'Luton', 'Aberdeen', 'Portsmouth', 'Milton Keynes',
  'Swansea', 'Oxford', 'Cambridge', 'York', 'Peterborough', 'Slough', 'Bournemouth', 'Ipswich',
  'Norwich', 'Dundee', 'Southend-on-Sea', 'Middlesbrough', 'Warrington', 'Swindon', 'Doncaster',
  'Preston', 'Gloucester', 'Bath', 'Chester', 'Exeter', 'Canterbury', 'Lancaster', 'Lincoln',
  'Wells', 'Durham', 'Winchester', 'Chichester', 'Ely', 'Ripon', 'Truro', 'St Davids', 'St Asaph',
  'Bangor', 'Armagh', 'Lisburn', 'Newry', 'Inverness', 'Stirling', 'Perth', 'Dunfermline',
  'Kirkcaldy', 'Glenrothes', 'Livingston', 'Cumbernauld', 'East Kilbride', 'Paisley', 'Greenock',
  'Dumfries', 'Ayr', 'Kilmarnock', 'Falkirk', 'Hamilton', 'Motherwell', 'Coatbridge'
]

const evolveAreas = ['studies', 'business', 'arts development', 'sports', 'general']
const enjoyAreas = ['gaming', 'content', 'humour', 'hiking', 'camping', 'sports']
const supportAreas = ['addiction', 'relationship', 'grief', 'illness', 'general depression', 'other']

const areaOptions = computed(() => {
  if (goal.value === 'evolve') return evolveAreas
  if (goal.value === 'enjoy') return enjoyAreas
  if (goal.value === 'support') return supportAreas
  return []
})

const areaLabel = computed(() => {
  if (goal.value === 'evolve') return 'Specify the area of your development'
  if (goal.value === 'enjoy') return "Specify your number 1 area of interests / hobbies"
  if (goal.value === 'support') return 'Specify the area of your struggles'
  return 'Area'
})

const detailsPlaceholder = computed(() => {
  if (goal.value === 'evolve') {
    const m = {
      studies: 'What are you studying, and at which level? Be specific.',
      business: 'How are you providing value to the world?',
      'arts development': "What is the art (e.g. music, painting) and what are the topics (genres) you're focused on?",
      sports: "What is the one sport you're the most focused on?",
      general: "Just write what you have to evolve in.",
    }
    return m[area.value] || 'Tell us about your development area.'
  }
  if (goal.value === 'enjoy') return 'Share a bit about your interests and how you like to spend time (up to 500 characters).'
  if (goal.value === 'support') {
    const m = {
      addiction: 'Specify what you are battling (e.g. gambling, drugs, alcoholism).',
      relationship: 'e.g. cheating, toxicity, or something else.',
      grief: 'Share what you feel comfortable sharing.',
      illness: 'Share what you feel comfortable sharing.',
      'general depression': 'Share what you feel comfortable sharing.',
      other: 'Describe your situation.',
    }
    return m[area.value] || 'Explain your struggles (up to 500 characters).'
  }
  return 'Details'
})

const thirdFieldLabel = computed(() => {
  if (goal.value === 'evolve') return 'Your goal'
  if (goal.value === 'enjoy') return 'How do you plan to enjoy your time together?'
  if (goal.value === 'support') return 'Resolution / Redemption'
  return 'Summary'
})

const thirdFieldPlaceholder = computed(() => {
  if (goal.value === 'evolve') return 'A specific goal connected to your area of development (max 100 characters)'
  if (goal.value === 'enjoy') return 'e.g. gaming, hiking (max 100 characters)'
  if (goal.value === 'support') return 'How are you hoping to resolve your issues or what do you hope to get comfortable with? (max 100 characters)'
  return ''
})

watch(goal, () => {
  area.value = ''
  details.value = ''
  thirdField.value = ''
})

async function submit() {
  if (!goal.value || !area.value || !details.value.trim() || !thirdField.value.trim() || !city.value.trim()) {
    errorMessage.value = 'Please fill all fields.'
    return
  }
  if (descriptionWordCount.value < minDescriptionWords) {
    errorMessage.value = 'Please add a bit more detail about your situation and goal so we can find better matches.'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    await api.post('/applications', {
      goal: goal.value,
      area: area.value,
      details: details.value.trim(),
      third_field: thirdField.value.trim(),
      city: city.value.trim(),
    })
    router.push('/suggestions')
  } catch (err) {
    errorMessage.value = err.response?.data?.error || err.message || 'Submission failed.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dashboard-title,
.dashboard-subtitle {
  font-family: 'Nunito', system-ui, sans-serif;
}
.dashboard-title {
  letter-spacing: -0.02em;
}
.dashboard-subtitle {
  font-weight: 600;
}
.typing-line {
  contain: layout style;
}
.overlay-desc {
  will-change: opacity;
}
.goal-hidden {
  opacity: 0;
  pointer-events: none;
}
.goal-revealed {
  opacity: 0;
  pointer-events: auto;
}
.goal-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem 1.5rem;
  margin-bottom: 1.5rem;
  direction: ltr;
}
@media (min-width: 640px) {
  .goal-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
.goal-inner {
  transform: translateZ(0);
}
.goal-img-bg {
  pointer-events: none;
}
</style>

<style>
@keyframes goalFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
