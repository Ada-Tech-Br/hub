import { ExternalLink, FileText, Archive, Globe, Lock } from "lucide-react";
import { Link } from "react-router-dom";
import type { ContentListItem } from "@/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ContentCardProps {
  content: ContentListItem;
}

const typeConfig = {
  project: {
    label: "Projeto",
    color: "bg-blue-50 text-blue-700 border-blue-200",
    iconBg: "bg-blue-100",
  },
  file: {
    label: "Arquivo",
    color: "bg-purple-50 text-purple-700 border-purple-200",
    iconBg: "bg-purple-100",
  },
};

function ContentTypeIcon({ content }: { content: ContentListItem }) {
  if (content.type === "project") return <Globe className="h-6 w-6 text-blue-600" />;
  if (content.file_type === "zip") return <Archive className="h-6 w-6 text-purple-600" />;
  return <FileText className="h-6 w-6 text-purple-600" />;
}

export function ContentCard({ content }: ContentCardProps) {
  const config = typeConfig[content.type];

  return (
    <Card className="group flex flex-col h-full hover:shadow-md transition-all duration-200 hover:-translate-y-0.5">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className={cn("flex h-12 w-12 shrink-0 items-center justify-center rounded-xl", config.iconBg)}>
            {content.icon ? (
              <span className="text-2xl">{content.icon}</span>
            ) : (
              <ContentTypeIcon content={content} />
            )}
          </div>
          <div className="flex flex-wrap gap-1.5">
            <Badge className={cn("text-xs border", config.color, "bg-transparent hover:bg-transparent")}>
              {config.label}
            </Badge>
            {!content.is_public && (
              <Badge variant="outline" className="text-xs gap-1">
                <Lock className="h-3 w-3" />
                Privado
              </Badge>
            )}
          </div>
        </div>
        <h3 className="font-semibold text-base leading-tight line-clamp-2 mt-3">{content.title}</h3>
      </CardHeader>

      <CardContent className="flex flex-col flex-1 gap-4 pt-0">
        {content.description && (
          <p className="text-sm text-muted-foreground line-clamp-2 flex-1">
            {content.description}
          </p>
        )}
        {!content.description && <div className="flex-1" />}

        <Button size="sm" className="w-full gap-2" asChild>
          <Link to={`/content/${content.id}`}>
            <ExternalLink className="h-4 w-4" />
            Acessar
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
