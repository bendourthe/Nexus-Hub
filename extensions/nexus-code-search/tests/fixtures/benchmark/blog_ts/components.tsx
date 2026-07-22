// React components for the blog reading experience.
import React from "react";

interface PostCardProps {
  title: string;
  slug: string;
  excerpt: string;
  onOpen: (slug: string) => void;
}

export function PostCard({ title, slug, excerpt, onOpen }: PostCardProps) {
  return (
    <article onClick={() => onOpen(slug)}>
      <h2>{title}</h2>
      <p>{excerpt}</p>
    </article>
  );
}

interface CommentListProps {
  comments: { id: number; body: string }[];
  loading: boolean;
}

export const CommentList: React.FC<CommentListProps> = ({ comments, loading }) => {
  if (loading) {
    return <div>Loading comments...</div>;
  }
  return (
    <ul>
      {comments.map((c) => (
        <li key={c.id}>{c.body}</li>
      ))}
    </ul>
  );
};

type PagerProps = { page: number; total: number; onPage: (n: number) => void };

export const Pager: React.FC<PagerProps> = ({ page, total, onPage }) => (
  <nav>
    <button disabled={page <= 1} onClick={() => onPage(page - 1)}>
      Prev
    </button>
    <span>
      {page} / {total}
    </span>
    <button disabled={page >= total} onClick={() => onPage(page + 1)}>
      Next
    </button>
  </nav>
);
