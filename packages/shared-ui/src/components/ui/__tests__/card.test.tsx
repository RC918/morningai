import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  CardAction,
} from '../card'

describe('Card', () => {
  it('renders card with all subcomponents', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>Card Description</CardDescription>
        </CardHeader>
        <CardContent>Card Content</CardContent>
        <CardFooter>Card Footer</CardFooter>
      </Card>
    )
    
    expect(screen.getByText('Card Title')).toBeInTheDocument()
    expect(screen.getByText('Card Description')).toBeInTheDocument()
    expect(screen.getByText('Card Content')).toBeInTheDocument()
    expect(screen.getByText('Card Footer')).toBeInTheDocument()
  })

  describe('Card interactive prop', () => {
    it('renders non-interactive card by default', () => {
      const { container } = render(<Card>Content</Card>)
      const card = container.firstChild as HTMLElement
      expect(card).not.toHaveClass('card-hover', 'cursor-pointer')
    })

    it('renders interactive card with hover styles', () => {
      const { container } = render(<Card interactive>Content</Card>)
      const card = container.firstChild as HTMLElement
      expect(card).toHaveClass('card-hover', 'cursor-pointer')
    })
  })

  it('handles click on interactive card', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(
      <Card interactive onClick={handleClick}>
        <CardContent>Clickable Card</CardContent>
      </Card>
    )
    
    const card = screen.getByText('Clickable Card').closest('div')!
    await user.click(card)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('renders CardHeader with CardAction in grid layout', () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
          <CardAction>
            <button>Action</button>
          </CardAction>
        </CardHeader>
      </Card>
    )
    
    const header = container.querySelector('[data-slot="card-header"]')
    expect(header).toHaveClass('has-data-[slot=card-action]:grid-cols-[1fr_auto]')
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
  })

  it('applies custom className to Card', () => {
    const { container } = render(<Card className="custom-card">Content</Card>)
    const card = container.firstChild as HTMLElement
    expect(card).toHaveClass('custom-card')
  })

  it('applies custom className to CardHeader', () => {
    const { container } = render(
      <Card>
        <CardHeader className="custom-header">Header</CardHeader>
      </Card>
    )
    const header = container.querySelector('[data-slot="card-header"]')
    expect(header).toHaveClass('custom-header')
  })

  it('applies custom className to CardTitle', () => {
    const { container } = render(
      <Card>
        <CardTitle className="custom-title">Title</CardTitle>
      </Card>
    )
    const title = container.querySelector('[data-slot="card-title"]')
    expect(title).toHaveClass('custom-title')
  })

  it('applies custom className to CardDescription', () => {
    const { container } = render(
      <Card>
        <CardDescription className="custom-desc">Description</CardDescription>
      </Card>
    )
    const desc = container.querySelector('[data-slot="card-description"]')
    expect(desc).toHaveClass('custom-desc')
  })

  it('applies custom className to CardContent', () => {
    const { container } = render(
      <Card>
        <CardContent className="custom-content">Content</CardContent>
      </Card>
    )
    const content = container.querySelector('[data-slot="card-content"]')
    expect(content).toHaveClass('custom-content')
  })

  it('applies custom className to CardFooter', () => {
    const { container } = render(
      <Card>
        <CardFooter className="custom-footer">Footer</CardFooter>
      </Card>
    )
    const footer = container.querySelector('[data-slot="card-footer"]')
    expect(footer).toHaveClass('custom-footer')
  })

  it('includes data-slot attributes for all subcomponents', () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
          <CardAction>Action</CardAction>
        </CardHeader>
        <CardContent>Content</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>
    )
    
    expect(container.querySelector('[data-slot="card"]')).toBeInTheDocument()
    expect(container.querySelector('[data-slot="card-header"]')).toBeInTheDocument()
    expect(container.querySelector('[data-slot="card-title"]')).toBeInTheDocument()
    expect(container.querySelector('[data-slot="card-description"]')).toBeInTheDocument()
    expect(container.querySelector('[data-slot="card-action"]')).toBeInTheDocument()
    expect(container.querySelector('[data-slot="card-content"]')).toBeInTheDocument()
    expect(container.querySelector('[data-slot="card-footer"]')).toBeInTheDocument()
  })

  it('forwards additional props to Card', () => {
    render(<Card data-testid="test-card">Content</Card>)
    expect(screen.getByTestId('test-card')).toBeInTheDocument()
  })

  it('renders complex nested content', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>
            <span>Complex</span> <strong>Title</strong>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
          </div>
        </CardContent>
      </Card>
    )
    
    expect(screen.getByText('Complex')).toBeInTheDocument()
    expect(screen.getByText('Title')).toBeInTheDocument()
    expect(screen.getByText('Paragraph 1')).toBeInTheDocument()
    expect(screen.getByText('Paragraph 2')).toBeInTheDocument()
  })

  it('renders empty card', () => {
    const { container } = render(<Card />)
    const card = container.firstChild as HTMLElement
    expect(card).toBeInTheDocument()
    expect(card).toHaveAttribute('data-slot', 'card')
  })

  it('positions CardAction in top-right corner', () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardAction>
            <button>⋮</button>
          </CardAction>
        </CardHeader>
      </Card>
    )
    
    const action = container.querySelector('[data-slot="card-action"]')
    expect(action).toHaveClass('col-start-2', 'row-span-2', 'row-start-1', 'self-start', 'justify-self-end')
  })
})
