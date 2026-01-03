# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development

- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm start` - Start production server

### Code Quality

- `npm run lint` - Run ESLint linter
- `npm run lint:fix` - Run ESLint with auto-fix
- `npm run prettier:check` - Check code formatting
- `npm run prettier:format` - Format code with Prettier

### Git Hooks

- `npm run lefthook:install` - Install git hooks (lefthook)
- `npm run lefthook:uninstall` - Uninstall git hooks

### Environment Setup

- Copy `.env.example` to `.env` before running the application
- Node.js 22+ is required for development
- The application runs on `http://localhost:3000`

## Architecture

This is a Next.js 15 beauty clinic clinic platform using **Feature Module Architecture** with strict module boundaries.

### Core Directory Structure

```
src/
├── modules/        # Feature modules with strict boundaries
│   ├── _common/    # Shared UI components (Button, Modal, Icon, etc.)
│   ├── clinic/     # Clinic feature
│   ├── reservation/# Reservation feature
│   ├── review/     # Review feature
│   └── layout/     # Global layout components
├── app/            # Next.js App Router pages
├── store/          # Zustand global state
├── apis/           # API clients
├── libs/           # External library configs
├── utils/          # Pure utility functions
└── i18n/           # Internationalization setup
```

### Module Boundaries (CRITICAL)

**Dependency Flow**: Feature Modules → \_common → Infrastructure

**Allowed imports:**

- Feature modules can import from `_common` and infrastructure layers
- Feature modules can import types from other features (types only)
- Pages can import from any feature module

**Forbidden imports:**

- Feature modules cannot import components/logic from other feature modules
- `_common` cannot import from feature modules
- Infrastructure cannot import from modules

**Exception (Types only):**

- `src/apis/**` may import **types only** from `src/modules/**/types` (domain models only)
  - ✅ Allowed: `import type { AlbumImage } from '@/modules/album/types'`
  - ❌ Forbidden: importing feature logic/components/hooks from `modules/**`

### Feature Module Structure

Each feature follows this pattern:

```
modules/[feature]/
├── components/     # Feature-specific components
├── types/         # TypeScript types
├── consts/        # Feature constants
└── hooks/         # Custom hooks (when needed)
```

### Component Organization Within Modules

**Component Placement Rules:**

#### 1. Parent Component Directory Structure

- **Single-use components**: Place inside parent component directory
- **Multi-use components**: Place at module root level

```
modules/clinic/components/
├── ClinicInfo/          # ✅ Reusable across multiple places
├── ClinicAddress/       # ✅ Reusable component
├── ClinicDetail/        # 🏗️ Parent component + exclusive children
│   ├── index.tsx        # Main parent component
│   ├── CasesSection/    # ✅ Only used in ClinicDetail
│   ├── DoctorInfo/      # ✅ Only used in ClinicDetail
│   ├── RecommendedTreatments/ # ✅ Only used in ClinicDetail
│   ├── ReviewsSection/  # ✅ Only used in ClinicDetail
│   └── ClinicDetailSkeleton/ # ✅ Only used in ClinicDetail
└── ClinicList/          # 🏗️ Another parent with its children
    ├── index.tsx
    ├── ClinicListSkeleton/
    └── ClinicTreatmentCard/
```

#### 2. Decision Criteria

**✅ Place INSIDE parent directory when:**

- Component is used **exclusively by one parent**
- Component represents a **specific section/feature** of the parent
- Component has **no meaning** outside the parent context
- Component is **tightly coupled** to parent's data structure

**✅ Place at MODULE ROOT when:**

- Component is **reusable across multiple parents**
- Component has **independent functionality**
- Component can be used in **different contexts/pages**
- Component represents a **standalone feature**

#### 3. Import Pattern Examples

```typescript
// ✅ Parent-specific component (nested path)
import CasesSection from "@/modules/clinic/components/ClinicDetail/CasesSection";
import DoctorInfo from "@/modules/clinic/components/ClinicDetail/DoctorInfo";

// ✅ Reusable component (root level)
import ClinicInfo from "@/modules/clinic/components/ClinicInfo";
import ClinicAddress from "@/modules/clinic/components/ClinicAddress";
```

#### 4. Benefits of This Structure

- **Clear Dependency Relationships**: Directory structure shows component usage scope
- **Refactoring Safety**: Parent-specific components can be moved/deleted with parent
- **Code Navigation**: Related components are physically co-located
- **Maintenance Clarity**: Immediately understand if component affects multiple places

## Custom Hooks Guidelines

### When to Create Custom Hooks

Create custom hooks for **UI/Logic separation** when:

- **Client interaction logic**: Input state, focus/keyboard handling, animation state, viewport/event subscriptions
- **Complex state + side effects**: Form validation + error display, polling/websocket subscriptions, intersection observer, multi-step modals
- **Testing & replaceability**: Keep components lightweight, test hooks independently with jest/msw
- **Component complexity explosion**: File exceeds 200-300 lines or has 3+ useEffect calls

### When Custom Hooks Are Overkill

Avoid custom hooks when:

- **Pure calculations/rules**: Date/amount formatting, schema validation, domain policies → Use pure functions/services instead
- **Server data fetching**: Use RSC direct fetch + Server Actions first. Only use client hooks when necessary
- **One-time use + simple state**: If separation hurts readability, keep logic in component

### Custom Hook Design Checklist

- **Naming**: `useXxx` (clear intent), return small API object
- **Input/Output**: Minimize arguments, encapsulate side effects inside hook
- **Dependencies**: Clear `useEffect`/`useCallback` deps, avoid tight coupling to external modules
- **Testing**: Complex logic hooks should have unit tests with `@testing-library/react` `renderHook`
- **Colocation**: Component-specific → same folder, Multi-use → `/hooks` or domain module
- **Performance**: Avoid large object returns, split unnecessary re-render causing state

### Architecture Boundaries

- **Server (data/auth/IO)**: RSC + Server Actions (`'use server'`)
- **Client (interaction/view state)**: Custom hooks (`'use client'`)
- **Domain logic**: Framework-agnostic pure functions/service modules

## Internationalization (CRITICAL)

This project has **ZERO TOLERANCE** for hard-coded text strings.

### Translation Usage

**Server Components (Preferred):**

```typescript
import { getTranslations } from "next-intl/server";

export default async function Component() {
  const t = await getTranslations("clinic.sections");
  return <h1>{t("title")}</h1>;
}
```

**Client Components (Only when necessary):**

```typescript
"use client";
import { useTranslations } from "next-intl";

export default function InteractiveComponent() {
  const t = useTranslations("common.modal");
  return <button>{t("closeButton")}</button>;
}
```

### Message Files

```
messages/
├── ja/             # Default language
│   ├── common.json # Shared UI elements
│   ├── home.json   # Home page specific
│   ├── clinic.json # Clinic feature
│   └── [feature].json
└── en/             # English translations
```

Use hierarchical keys: `module.component.key` format.

## Technology Stack

- **Framework**: Next.js 15 with App Router, standalone output
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS v4 with CSS custom properties
- **State Management**:
  - Zustand for client state management
  - React Query (@tanstack/react-query) for server state management
- **Internationalization**: next-intl (default: Japanese, supported: English, Japanese)
- **Linting**: ESLint + Prettier with automated import sorting
- **Git Hooks**: lefthook for pre-commit hooks

## Data Fetching Guidelines

This project uses different data fetching strategies based on component type:

### Server vs Client Data Fetching

| Component Type   | Method                  | Use Case                                                   |
| ---------------- | ----------------------- | ---------------------------------------------------------- |
| Server Component | Direct `apiClient` call | Initial page load, SEO-required content                    |
| Client Component | React Query hooks       | Forms, mutations, real-time updates, client-side filtering |

### Server Component Pattern (Do NOT use React Query)

```typescript
// ✅ Use direct apiClient call in server components
import { getSomeData } from "@/apis/someApi";

export default async function ServerPage() {
  const data = await getSomeData();
  return <div>{data.title}</div>;
}
```

**When to use:**

- Leverage Next.js `fetch` + `revalidate` caching
- SEO-optimized content
- Initial page data loading

### Client Component Pattern (Use React Query)

```typescript
// ✅ Use React Query hooks in client components
"use client";
import { useGetSomeData } from "@/apis/someApi/queries";

export default function ClientComponent() {
  const { data, isLoading, error } = useGetSomeData();

  if (isLoading) return <Skeleton />;
  if (error) return <Error />;

  return <div>{data.title}</div>;
}
```

**When to use:**

- Data fetching after user interaction
- Form submissions, mutations
- Real-time updates, polling
- Optimistic updates

### React Query File Structure

```
src/
├── libs/
│   ├── queryClient.ts    # QueryClient configuration
│   └── queryKeys.ts      # Query key factory
├── apis/
│   └── [feature]/
│       ├── index.ts      # API functions (shared by server/client)
│       └── queries.ts    # React Query hooks (client only)
└── app/
    └── providers.tsx     # QueryClientProvider wrapper
```

### Query Key Management

Always use the `queryKeys` factory for type-safe cache management:

```typescript
// ✅ Good - Type-safe query key
queryKey: queryKeys.auth.detail(id);

// ❌ Bad - Manual query key
queryKey: ["auth", "detail", id];
```

### React Query Hook Patterns

**Mutation Example (POST/PUT/DELETE):**

```typescript
// src/apis/auth/queries.ts
"use client";

import { useMutation } from "@tanstack/react-query";
import { authLogin } from "./index";

export const useAuthLogin = (options?) => {
  return useMutation({
    mutationFn: authLogin,
    ...options,
  });
};
```

**Query Example (GET):**

```typescript
// src/apis/staff/queries.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/libs/queryKeys";
import { getStaffDetail } from "./index";

export const useGetStaffDetail = (id: number, options?) => {
  return useQuery({
    queryKey: queryKeys.auth.detail(id),
    queryFn: () => getStaffDetail(id),
    enabled: !!id, // Only fetch when id exists
    ...options,
  });
};
```

### Cache Invalidation

```typescript
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/libs/queryKeys";

const queryClient = useQueryClient();

// Invalidate specific item
queryClient.invalidateQueries({ queryKey: queryKeys.auth.detail(id) });

// Invalidate all auth queries
queryClient.invalidateQueries({ queryKey: queryKeys.auth.all });
```

### Best Practices

1. **Use query keys from factory** - Ensures type safety and consistency
2. **Handle all states** - Always handle `isLoading`, `isError`, and success states
3. **Enable conditionally** - Use `enabled` option to control when queries run
4. **Invalidate after mutations** - Keep cache fresh after data changes

## Key Libraries & Tools

- `@adventureinc/wc`: Web components library
- `tailwind-merge`: Tailwind class merging utility
- `clsx`: Class name utility
- `zod`: Schema validation
- `js-cookie`: Cookie handling

### ESLint Configuration

Key rules enforced:

- Prohibited `React.FC` usage (use regular function components)
- Import/export sorting with `simple-import-sort`
- Console warnings in development
- TypeScript strict type checking

## Development Guidelines

### TypeScript Rules

- Never use `any` type
- Define complex types in separate `types/` directories
- Use generics for reusable components

### Type Ownership Rules (Domain vs API DTO) (CRITICAL)

Keep type ownership clear and avoid duplicating the same shape across layers.

**Domain (feature) types**

- Place domain model types in `src/modules/[feature]/types/`
  - Examples: `AlbumCategory`, `AlbumImage`, `AlbumTab`, UI state types like `AlbumState`
- These types represent the **business/domain shape**, and can be reused across UI/components/hooks.

**API DTO types**

- Place API request/response DTO types in `src/apis/[feature]/index.ts`
  - Examples: `GetXxxResponse`, `CreateXxxRequest`, `SignedUrlResponse`
- API DTOs may reference domain model types when the API payload matches the domain shape:
  - Example: `interface AlbumResponse { mainImages: AlbumImage[]; ... }`

**File organization rule for `src/apis/[feature]/index.ts`**

- Define each API’s DTO types **directly above the API function that uses them**
- Keep the API file free of domain model definitions (import domain types from `modules/**/types` instead)

#### Interface vs Type Usage Rules

**Basic Principles**:

- **Object Shapes (Props/DTO/Domain Entities)**: Use `interface`
- **Union/Type Aliases/Tuples/Function Types/Advanced Type Compositions**: Use `type`

**Exceptions**:

- **External Type Extensions (Global/Module Augmentation)**: Always use `interface`
- **One-time Local Function Types**: Simply define with `type` alias

**✅ Correct Usage Examples**:

```typescript
// ✅ Object shape - use interface
interface UserProps {
  id: string;
  name: string;
  email?: string;
}

// ✅ Union type - use type
type Status = "loading" | "success" | "error";

// ✅ Function type - use type
type EventHandler = (event: MouseEvent) => void;

// ✅ External type extension - use interface
declare global {
  interface Window {
    gtag: (command: string, ...args: unknown[]) => void;
  }
}

// ✅ Complex type composition - use type
type ApiResponse<T> = {
  data: T;
  status: "success" | "error";
  message?: string;
};

// ✅ Tuple type - use type
type Coordinates = [number, number];
```

**❌ Incorrect Usage Examples**:

```typescript
// ❌ Object shape with type (should use interface)
type UserProps = {
  id: string;
  name: string;
};

// ❌ Union type with interface (should use type)
interface Status {
  loading: never;
  success: never;
  error: never;
}
```

### Component Rules

- Functional components only (no class components)
- Server components by default - use `'use client'` only when needed
- Keep components under 200 lines
- Always define explicit Props interfaces
- Follow this structure: state → handlers → effects → render

### File Naming

- Feature modules: lowercase with hyphens (`clinic`, `reservation`)
- Components: PascalCase folders/files (`ClinicDetail/`, `ClinicDetail.tsx`)
- Types: kebab-case with `.types.ts` suffix
- Constants: kebab-case with `.consts.ts` suffix
- Hooks: camelCase with `use` prefix

### Import Patterns

Use absolute imports with `@/` prefix:

```typescript
import { Button } from "@/modules/_common/components/Button";
import { useStore } from "@/store/useStore";
import { ClinicType } from "@/modules/clinic/types";
```

## Styling Guidelines

### CSS Variables Usage (CRITICAL)

- **ALWAYS** use CSS variables defined in `@/app/globals.css` instead of hard-coded colors
- Use Tailwind classes that map to CSS variables for consistency

**Complete Color System:**

```css
/* Primary Colors */
--color-primary: #ffc11c;           → bg-primary, text-primary
--color-primary-dark: #e6ae19;      → bg-primary-dark, text-primary-dark
--color-primary-light: #fff9e1;     → bg-primary-light, text-primary-light

/* Secondary Colors */
--color-secondary: #1ba1ff;         → bg-secondary, text-secondary
--color-secondary-dark: #1891e6;    → bg-secondary-dark, text-secondary-dark
--color-secondary-darker: #1c5db5;  → bg-secondary-darker, text-secondary-darker
--color-secondary-light: #d1ecff;   → bg-secondary-light, text-secondary-light

/* Neutral Colors */
--color-white: #ffffff;             → bg-white, text-white
--color-black: #222222;             → bg-black, text-black
--color-gray: #a6a6a6;              → bg-gray, text-gray
--color-gray-dark: #4d4d4d;         → bg-gray-dark, text-gray-dark
--color-gray-light: #d1d1d1;        → bg-gray-light, border-gray-light
--color-gray-lighter: #e4e4e4;      → bg-gray-lighter, border-gray-lighter
--color-gray-lightness: #f4f4f4;    → bg-gray-lightness, border-gray-lightness

/* Status Colors */
--color-error: #ff1d1c;             → bg-error, text-error
--color-error-light: #fff4f4;       → bg-error-light, text-error-light

/* Border Radius */
--radius: 3px;                      → rounded-[--radius]
```

**Bad:**

```jsx
className = "bg-[#f4f4f4] border-[#e4e4e4] text-[#1c5db5]";
```

**Good:**

```jsx
className = "bg-gray-lightness border-gray-lighter text-secondary-darker";
```

### Font Guidelines

- **DO NOT** set custom font families in components
- Rely on the global font configuration defined in the project
- Avoid inline font-family styles unless absolutely necessary for special cases

### Figma Design Integration

When implementing Figma designs:

1. **Use Figma Dev Mode tools** to extract exact design specifications
2. **Map Figma colors to CSS variables** rather than copying hex values directly
3. **Prioritize existing component library** (`@/modules/_common/components/`) over custom implementations
4. **Maintain responsive design principles** even when Figma shows fixed dimensions

## Component Design Patterns

### Modal Components

- **Use existing modal components** (`SlideUpModal`, `Modal`) instead of creating new ones
- SlideUpModal provides:
  - Built-in close button with proper positioning
  - Header with title
  - Consistent slide-up animation
  - Proper z-index layering

```jsx
<SlideUpModal isOpen={isOpen} onClose={onClose} title={t("title")}>
  {/* Content goes here */}
</SlideUpModal>
```

### State Management Patterns

- **Single selection state**: Use `string | null` for optional single selection
- **Multiple selection state**: Use `string[]` for multiple selections
- **Handler naming**:
  - Single: `onItemChange: (id: string | null) => void`
  - Multiple: `onItemsChange: (ids: string[]) => void`

### UI Selection Patterns

**Left Sidebar Tabs (Single Selection):**

```jsx
// State
const [selectedId, setSelectedId] = useState<string | null>(null);

// Handler
const handleSelect = (id: string) => {
  setSelectedId(id === selectedId ? null : id);
};

// Styling
className={`${selectedId === id ? 'bg-secondary-darker text-white' : 'bg-gray-lightness text-gray'}`}
```

**Tag Buttons (Multiple Selection):**

```jsx
// State
const [selectedIds, setSelectedIds] = useState<string[]>([]);

// Handler
const handleToggle = (id: string) => {
  const newSelection = selectedIds.includes(id)
    ? selectedIds.filter(selectedId => selectedId !== id)
    : [...selectedIds, id];
  setSelectedIds(newSelection);
};

// Styling
className={`${selectedIds.includes(id) ? 'bg-secondary-light text-secondary-darker border-secondary-darker' : 'bg-white text-gray-dark border-gray-lighter'}`}
```

## Critical Rules

1. **Never hard-code text** - Always use i18n message keys
2. **Never hard-code colors** - Always use CSS variables via Tailwind classes
3. **Respect module boundaries** - No cross-feature component imports
4. **Server-first approach** - Use server components unless interactivity required
5. **Type safety** - No `any` types, explicit interfaces for all props
6. **Architecture consistency** - Follow established patterns and directory structure
7. **Reuse existing components** - Check `@/modules/_common/components/` before creating new ones

When adding new features:

1. Create feature module in appropriate directory
2. Plan message structure before implementation
3. Follow dependency rules strictly
4. Use `_common` only for pure UI components
5. Add translations for all supported languages
6. Map design colors to existing CSS variables
7. Reuse existing modal and form components
