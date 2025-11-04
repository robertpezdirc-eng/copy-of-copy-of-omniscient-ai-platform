import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd'
import { api } from '../lib/api'

interface DashboardItem {
  id: string
  name: string
  url: string
}

interface DashboardCategory {
  id: string
  name: string
  dashboards: DashboardItem[]
}

const initialCategories: DashboardCategory[] = [
  {
    id: 'core',
    name: 'Core Views',
    dashboards: [
      { id: 'core-health', name: 'System Health', url: '/health' },
      { id: 'core-pricing', name: 'Pricing & Plans', url: '/pricing' },
      { id: 'core-profile', name: 'Profile', url: '/profile' },
      { id: 'core-admin', name: 'Admin', url: '/admin' },
      { id: 'core-affiliate', name: 'Affiliate', url: '/affiliate' },
      { id: 'core-bi', name: 'BI Dashboard', url: '/bi-dashboard' },
    ],
  },
  {
    id: 'workspace',
    name: 'Workspace',
    dashboards: [
      { id: 'ws-crm', name: 'CRM', url: '/crm' },
      { id: 'ws-reports', name: 'Reports', url: '/reports' },
      { id: 'ws-notifications', name: 'Notifications', url: '/notifications' },
      { id: 'ws-settings', name: 'Settings', url: '/settings' },
      { id: 'ws-assistant', name: 'Assistant', url: '/assistant' },
    ],
  },
  {
    id: 'finance',
    name: 'Finance',
    dashboards: [
      { id: 'fin-1', name: 'Finance', url: '/finance' },
      { id: 'fin-2', name: 'Revenue Trends', url: '/module/revenue-trends' },
      { id: 'fin-3', name: 'Cost Analysis', url: '/module/cost-analysis' },
      { id: 'fin-4', name: 'Profit & Loss', url: '/module/profit-loss' },
      { id: 'fin-5', name: 'Forecasting', url: '/module/forecasting' },
      { id: 'fin-6', name: 'Finance 2', url: '/finance2' },
    ],
  },
  {
    id: 'analytics',
    name: 'Analytics',
    dashboards: [
      { id: 'ana-1', name: 'Analytics', url: '/analytics' },
      { id: 'ana-2', name: 'Segmentation', url: '/module/segmentation' },
      { id: 'ana-3', name: 'Cohorts', url: '/module/cohorts' },
      { id: 'ana-4', name: 'Attribution', url: '/module/attribution' },
      { id: 'ana-5', name: 'Funnels', url: '/module/funnels' },
      { id: 'ana-6', name: 'Analytics 2', url: '/analytics2' },
    ],
  },
  {
    id: 'projects',
    name: 'Projects',
    dashboards: [
      { id: 'prj-1', name: 'Projects Overview', url: '/projects' },
      { id: 'prj-2', name: 'Roadmap', url: '/module/roadmap' },
      { id: 'prj-3', name: 'Sprint Boards', url: '/module/sprint-boards' },
      { id: 'prj-4', name: 'Resources', url: '/module/resources' },
      { id: 'prj-5', name: 'Risks', url: '/module/risks' },
      { id: 'prj-6', name: 'Projects 2', url: '/projects2' },
    ],
  },
  {
    id: 'ops',
    name: 'Operations',
    dashboards: [
      { id: 'ops-1', name: 'Sales', url: '/sales' },
      { id: 'ops-2', name: 'Marketing', url: '/marketing' },
      { id: 'ops-3', name: 'Operations', url: '/operations' },
    ],
  },
]

const MainDashboard: React.FC = () => {
  const [categories, setCategories] = useState<DashboardCategory[]>(() => {
    const saved = localStorage.getItem('main-dashboard-layout')
    return saved ? JSON.parse(saved) : initialCategories
  })

  useEffect(() => {
    let mounted = true
    // Load from backend (production-like), then fallback to localStorage
    api.get('/layout')
      .then((res) => {
        const backendCats = res.data?.categories
        if (mounted && Array.isArray(backendCats)) {
          // Merge backend-provided categories with local extended set to keep 25+
          // Strategy: keep local extended, but ensure core from backend is present
          const coreFromBackend = backendCats.find((c: any) => c.id === 'core')
          if (coreFromBackend) {
            const merged = [
              { ...coreFromBackend },
              ...initialCategories.filter((c) => c.id !== 'core')
            ]
            setCategories(merged)
            localStorage.setItem('main-dashboard-layout', JSON.stringify(merged))
          }
        }
      })
      .catch(() => { /* silent fallback */ })
    return () => { mounted = false }
  }, [])

  const onDragEnd = (result: DropResult) => {
    const { source, destination } = result
    if (!destination) return

    if (source.droppableId === destination.droppableId) {
      const category = categories.find((c) => c.id === source.droppableId)
      if (!category) return
      const newDashboards = Array.from(category.dashboards)
      const [moved] = newDashboards.splice(source.index, 1)
      newDashboards.splice(destination.index, 0, moved)

      const newCategories = categories.map((c) =>
        c.id === category.id ? { ...c, dashboards: newDashboards } : c
      )
      setCategories(newCategories)
    } else {
      const sourceCat = categories.find((c) => c.id === source.droppableId)
      const destCat = categories.find((c) => c.id === destination.droppableId)
      if (!sourceCat || !destCat) return

      const sourceDashboards = Array.from(sourceCat.dashboards)
      const destDashboards = Array.from(destCat.dashboards)

      const [moved] = sourceDashboards.splice(source.index, 1)
      destDashboards.splice(destination.index, 0, moved)

      const newCategories = categories.map((c) => {
        if (c.id === sourceCat.id) return { ...c, dashboards: sourceDashboards }
        if (c.id === destCat.id) return { ...c, dashboards: destDashboards }
        return c
      })
      setCategories(newCategories)
    }

    // Persist to backend (best effort) and localStorage for speed
    try { api.put('/layout', { categories }) } catch {}
    try { localStorage.setItem('main-dashboard-layout', JSON.stringify(categories)) } catch {}
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Main Dashboard</h1>
      <p>Drag & drop dashboards to reorder or move between categories</p>

      <DragDropContext onDragEnd={onDragEnd}>
        {categories.map((cat) => (
          <Droppable droppableId={cat.id} key={cat.id}>
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                style={{
                  marginBottom: '2rem',
                  padding: '1rem',
                  border: '1px solid #ccc',
                  borderRadius: '8px',
                  backgroundColor: '#fafafa',
                }}
              >
                <h2 style={{ marginTop: 0 }}>{cat.name}</h2>
                {cat.dashboards.map((dash, index) => (
                  <Draggable draggableId={dash.id} index={index} key={dash.id}>
                    {(dragProvided) => (
                      <Link
                        to={dash.url}
                        ref={dragProvided.innerRef}
                        {...dragProvided.draggableProps}
                        {...dragProvided.dragHandleProps}
                        style={{
                          ...dragProvided.draggableProps.style,
                          display: 'block',
                          padding: '1rem',
                          marginBottom: '0.5rem',
                          border: '1px solid #999',
                          borderRadius: '8px',
                          backgroundColor: '#f1f1f1',
                          textDecoration: 'none',
                          color: '#333',
                        }}
                      >
                        {dash.name}
                      </Link>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        ))}
      </DragDropContext>
    </div>
  )
}

export default MainDashboard